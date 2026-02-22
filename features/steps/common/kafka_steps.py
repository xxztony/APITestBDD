from __future__ import annotations

import re

from behave import given, when

from src.core.messaging.kafka_client import KafkaClient


def _get_data(context):
    return getattr(context, "http_data", None) or getattr(context, "data", None)


def _require_kafka_client(context) -> KafkaClient:
    client = getattr(context, "kafka_client", None)
    if client is None:
        raise AssertionError("context.kafka_client is required for Kafka steps")
    return client


def _resolve_offset_expr(data, expr: str) -> int:
    expr = expr.strip()
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    match = re.fullmatch(r"\$\{([^}]+)\}", expr)
    if not match:
        raise AssertionError(f"Invalid offset expression '{expr}'. Use integer or ${'{var}'}")
    var_name = match.group(1)
    try:
        raw = data.get_var(var_name)
    except KeyError as exc:
        raise AssertionError(f"Missing variable '{var_name}' for offset expression") from exc
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise AssertionError(f"Variable '{var_name}' is not an int: {raw!r}") from exc


@given('I store Kafka topic "{topic}" partition {partition:d} end offset as "{var_name}"')
def step_store_kafka_end_offset(context, topic: str, partition: int, var_name: str) -> None:
    data = _get_data(context)
    client = _require_kafka_client(context)
    offset = client.get_end_offset(topic=topic, partition=partition)
    data.put_var(var_name, offset, overwrite=True)
    data.common.setdefault("kafka", {})[var_name] = offset


@when(
    'I read Kafka messages from topic "{topic}" partition {partition:d} '
    'at offset "{offset_expr}" offset shift {shift:d}'
)
def step_read_kafka_messages_with_shift(
    context,
    topic: str,
    partition: int,
    offset_expr: str,
    shift: int,
) -> None:
    data = _get_data(context)
    client = _require_kafka_client(context)
    base_offset = _resolve_offset_expr(data, offset_expr)
    offset = base_offset + shift
    messages = client.consume_from_offset(topic=topic, partition=partition, offset=offset)
    data.common.setdefault("kafka", {})["messages"] = messages
    data.common.setdefault("kafka", {})["message"] = messages[0] if messages else None

PYCODE
