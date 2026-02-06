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
            return
        except Exception as exc:  # noqa: BLE001
            raise KafkaClientError("confluent-kafka is required for KafkaClient") from exc

    def close(self) -> None:
        if self._producer:
            self._producer.flush(10)
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
        self._produce_confluent(topic, value, key=key, headers=headers, timeout=timeout)

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

    def subscribe(self, topics: Iterable[str]) -> None:
        assert self._consumer is not None
        self._consumer.subscribe(list(topics))

    def consume(self, timeout: float = 1.0) -> KafkaMessage | None:
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

    def get_end_offset(self, topic: str, partition: int = 0, timeout: float = 5.0) -> int:
        try:
            from confluent_kafka import TopicPartition
        except Exception as exc:  # noqa: BLE001
            raise KafkaClientError("confluent-kafka is required for KafkaClient") from exc

        assert self._consumer is not None
        tp = TopicPartition(topic, partition)
        _, high = self._consumer.get_watermark_offsets(tp, timeout=timeout)
        return int(high)

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


if __name__ == "__main__":
    kafka = KafkaClient(
        bootstrap_servers="broker1:9092,broker2:9092",
        scenario_id="offset-check",
    )
    try:
        end_offset = kafka.get_end_offset(topic="my_topic", partition=0, timeout=5.0)
        print(f"end_offset: {end_offset}")
    finally:
        kafka.close()
