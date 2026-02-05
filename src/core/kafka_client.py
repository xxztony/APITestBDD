from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping


logger = logging.getLogger(__name__)


class KafkaClientError(RuntimeError):
    pass


@dataclass(slots=True)
class KafkaMessage:
    topic: str
    key: bytes | None
    value: bytes | None
    headers: dict[str, bytes] | None
    timestamp_ms: int | None


class KafkaClient:
    def __init__(
        self,
        bootstrap_servers: str,
        *,
        scenario_id: str | None = None,
        group_prefix: str = "e2e",
        security_config: Mapping[str, Any] | None = None,
    ) -> None:
        if not bootstrap_servers:
            raise ValueError("bootstrap_servers is required")
        self._bootstrap_servers = bootstrap_servers
        self._scenario_id = scenario_id or str(uuid.uuid4())
        self._group_id = f"{group_prefix}-{self._scenario_id}"
        self._security_config = dict(security_config or {})

        self._producer = None
        self._consumer = None
        self._backend = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from confluent_kafka import Consumer, Producer

            producer_config = {"bootstrap.servers": self._bootstrap_servers}
            producer_config.update(self._security_config)
            consumer_config = {
                "bootstrap.servers": self._bootstrap_servers,
                "group.id": self._group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
            consumer_config.update(self._security_config)
            self._producer = Producer(producer_config)
            self._consumer = Consumer(consumer_config)
            self._backend = "confluent"
            return
        except Exception:
            pass

        try:
            from kafka import KafkaConsumer, KafkaProducer

            producer_kwargs = {"bootstrap_servers": self._bootstrap_servers}
            producer_kwargs.update(self._security_config)
            consumer_kwargs = {
                "bootstrap_servers": self._bootstrap_servers,
                "group_id": self._group_id,
                "auto_offset_reset": "earliest",
                "enable_auto_commit": False,
                "consumer_timeout_ms": 1000,
            }
            consumer_kwargs.update(self._security_config)
            self._producer = KafkaProducer(**producer_kwargs)
            self._consumer = KafkaConsumer(**consumer_kwargs)
            self._backend = "kafka-python"
            return
        except Exception as exc:  # noqa: BLE001
            raise KafkaClientError(
                "Kafka backend not available; install confluent-kafka or kafka-python"
            ) from exc

    def close(self) -> None:
        if self._backend == "confluent":
            if self._producer:
                self._producer.flush(10)
            if self._consumer:
                self._consumer.close()
        elif self._backend == "kafka-python":
            if self._producer:
                self._producer.flush(timeout=10)
                self._producer.close()
            if self._consumer:
                self._consumer.close()

    def produce(
        self,
        topic: str,
        value: Any,
        *,
        key: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float = 10.0,
    ) -> None:
        if self._backend == "confluent":
            self._produce_confluent(topic, value, key=key, headers=headers, timeout=timeout)
            return
        self._produce_kafka_python(topic, value, key=key, headers=headers, timeout=timeout)

    def _produce_confluent(
        self,
        topic: str,
        value: Any,
        *,
        key: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float,
    ) -> None:
        assert self._producer is not None

        errors: list[str] = []

        def _delivery(err, msg) -> None:  # type: ignore[no-untyped-def]
            if err is not None:
                errors.append(str(err))

        payload = self._encode_value(value)
        k = self._encode_key(key)
        hdrs = self._encode_headers(headers)
        self._producer.produce(topic, value=payload, key=k, headers=hdrs, callback=_delivery)
        self._producer.flush(timeout)
        if errors:
            raise KafkaClientError(f"Kafka produce failed: {errors[0]}")

    def _produce_kafka_python(
        self,
        topic: str,
        value: Any,
        *,
        key: str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float,
    ) -> None:
        assert self._producer is not None
        payload = self._encode_value(value)
        k = self._encode_key(key)
        hdrs = self._encode_headers(headers)
        future = self._producer.send(topic, value=payload, key=k, headers=hdrs)
        future.get(timeout=timeout)

    def subscribe(self, topics: Iterable[str]) -> None:
        if self._backend == "confluent":
            assert self._consumer is not None
            self._consumer.subscribe(list(topics))
        else:
            assert self._consumer is not None
            self._consumer.subscribe(list(topics))

    def consume(self, timeout: float = 1.0) -> KafkaMessage | None:
        if self._backend == "confluent":
            assert self._consumer is not None
            msg = self._consumer.poll(timeout)
            if msg is None:
                return None
            if msg.error():
                raise KafkaClientError(f"Kafka consume error: {msg.error()}")
            return KafkaMessage(
                topic=msg.topic(),
                key=msg.key(),
                value=msg.value(),
                headers=dict(msg.headers() or {}),
                timestamp_ms=msg.timestamp()[1] if msg.timestamp() else None,
            )

        assert self._consumer is not None
        records = self._consumer.poll(timeout_ms=int(timeout * 1000))
        if not records:
            return None
        for _, messages in records.items():
            for msg in messages:
                timestamp = msg.timestamp
                if isinstance(timestamp, tuple):
                    timestamp = timestamp[1]
                return KafkaMessage(
                    topic=msg.topic,
                    key=msg.key,
                    value=msg.value,
                    headers=dict(msg.headers or []),
                    timestamp_ms=timestamp,
                )
        return None

    def wait(
        self,
        topic: str,
        predicate: Callable[[KafkaMessage], bool] | None = None,
        *,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
    ) -> KafkaMessage:
        self.subscribe([topic])
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.consume(timeout=poll_interval)
            if msg is None:
                continue
            if predicate is None:
                return msg
            try:
                if predicate(msg):
                    return msg
            except Exception as exc:  # noqa: BLE001
                raise KafkaClientError(f"Predicate failed: {exc}") from exc
        raise KafkaClientError(f"Timeout waiting for message on {topic} after {timeout}s")

    @staticmethod
    def _encode_value(value: Any) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode("utf-8")
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _encode_key(key: str | bytes | None) -> bytes | None:
        if key is None:
            return None
        return key if isinstance(key, bytes) else key.encode("utf-8")

    @staticmethod
    def _encode_headers(headers: Mapping[str, str] | None) -> list[tuple[str, bytes]] | None:
        if not headers:
            return None
        return [(k, v.encode("utf-8")) for k, v in headers.items()]
