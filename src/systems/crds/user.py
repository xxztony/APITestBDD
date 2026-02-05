from __future__ import annotations

import json
import logging
from typing import Any, Mapping

from src.clients.crds.user_client import CrdsUserClient
from src.core.config import Config
from src.core.db_client import DbClient
from src.core.http_client import HttpClient, HttpResponse
from src.core.kafka_client import KafkaClient, KafkaMessage
from src.payloads.crds.create_user import CreateUserRequest


class CRDSUser:
    def __init__(self, context: Any) -> None:
        self._context = context
        self._logger = self._get_context_value("logger", default=logging.getLogger(__name__))
        self._config = self._get_context_value("config", default=None)

        http_client: HttpClient | None = self._get_context_value("http_client", default=None)
        self._http_client = http_client
        self._kafka_client = self._get_context_value("kafka_client", default=None)
        self._db_client = self._get_context_value("db_client", default=None)

        if self._http_client is None:
            raise ValueError("context.http_client is required")
        self._client = CrdsUserClient(self._http_client)

    def create_user(
        self,
        payload: CreateUserRequest,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        schema: Any | None = None,
        validate_schema: bool | None = None,
    ) -> HttpResponse:
        return self._client.create_user(
            payload,
            headers=headers,
            timeout=timeout,
            schema=schema,
            validate_schema=validate_schema,
        )

    def create_user_and_verify(
        self,
        payload: CreateUserRequest,
        *,
        kafka_topic: str | None = None,
        kafka_timeout: float = 10.0,
        db_table: str | None = None,
        db_id_column: str = "id",
        db_email_column: str = "email",
    ) -> dict[str, Any]:
        if self._kafka_client is None:
            raise ValueError("context.kafka_client is required for create_user_and_verify")
        if self._db_client is None:
            raise ValueError("context.db_client is required for create_user_and_verify")

        response = self.create_user(payload)
        response_json = response.json
        if not isinstance(response_json, Mapping):
            raise RuntimeError("Create user response is not JSON object")

        user_id = self._extract_user_id(response_json)
        topic = kafka_topic or self._config_value("crds.kafka.user_topic")
        if not topic:
            raise ValueError("Kafka topic is required via parameter or config crds.kafka.user_topic")

        message = self._kafka_client.wait(
            topic=topic,
            predicate=lambda msg: self._match_user_created(msg, user_id, payload.email),
            timeout=kafka_timeout,
        )

        table = db_table or self._config_value("crds.db.user_table")
        if not table:
            raise ValueError("DB table is required via parameter or config crds.db.user_table")
        record = self._fetch_user_record(
            table=table,
            user_id=user_id,
            email=payload.email,
            id_column=db_id_column,
            email_column=db_email_column,
        )
        if record is None:
            raise RuntimeError(f"User record not found in DB table {table}")

        return {
            "response": response,
            "event": message,
            "db_record": record,
        }

    def _fetch_user_record(
        self,
        *,
        table: str,
        user_id: str | None,
        email: str,
        id_column: str,
        email_column: str,
    ) -> dict[str, Any] | None:
        assert self._db_client is not None
        if user_id:
            query = f"SELECT * FROM {table} WHERE {id_column} = ?"
            record = self._db_client.select_one(query, params=[user_id])
            if record is not None:
                return record
        query = f"SELECT * FROM {table} WHERE {email_column} = ?"
        return self._db_client.select_one(query, params=[email])

    def _match_user_created(
        self,
        message: KafkaMessage,
        user_id: str | None,
        email: str,
    ) -> bool:
        data = self._decode_message(message.value)
        if not isinstance(data, Mapping):
            return False
        event_type = (
            data.get("event_type")
            or data.get("eventType")
            or data.get("type")
            or data.get("name")
        )
        if str(event_type) != "USER_CREATED":
            return False
        if user_id and str(data.get("id") or data.get("userId") or data.get("user_id")) != str(user_id):
            return False
        if email and str(data.get("email")) != str(email):
            return False
        return True

    @staticmethod
    def _decode_message(value: bytes | None) -> Any:
        if value is None:
            return None
        if isinstance(value, bytes):
            try:
                text = value.decode("utf-8")
                return json.loads(text)
            except Exception:
                return value
        return value

    @staticmethod
    def _extract_user_id(data: Mapping[str, Any]) -> str | None:
        value = data.get("id") or data.get("userId") or data.get("user_id")
        return str(value) if value is not None else None

    def _get_context_value(self, key: str, default: Any) -> Any:
        if hasattr(self._context, key):
            return getattr(self._context, key)
        if isinstance(self._context, Mapping):
            return self._context.get(key, default)
        return default

    def _config_value(self, key: str) -> Any:
        if isinstance(self._config, Config):
            return self._config.get(key)
        return None
