from __future__ import annotations

import logging
from dataclasses import dataclass

from hooks.resources.registry import ResourceRegistry

logger = logging.getLogger(__name__)

try:
    from src.core.messaging.kafka_client import KafkaClient  # type: ignore
except Exception:  # noqa: BLE001
    KafkaClient = None  # type: ignore


@dataclass
class KafkaRuntime:
    client: any

    def close(self) -> None:
        if self.client and hasattr(self.client, "close"):
            self.client.close()


def ensure_kafka(context) -> KafkaRuntime:
    registry: ResourceRegistry = context.resources
    if registry.has("kafka"):
        runtime: KafkaRuntime = registry.get("kafka")
        registry.mark_enabled("kafka")
        context.kafka_client = runtime.client
        return runtime

    if KafkaClient is None:
        raise RuntimeError("KafkaClient implementation not available; cannot enable @kafka")

    bootstrap = context.config_obj.get("kafka.bootstrap_servers") or context.config_obj.get("crds.kafka.bootstrap_servers")
    if not bootstrap:
        raise ValueError("Missing kafka.bootstrap_servers or crds.kafka.bootstrap_servers for @kafka")

    client = KafkaClient(
        bootstrap_servers=bootstrap,
        scenario_id=getattr(context, "scenario_id", None) or "scenario",
        group_prefix="e2e",
    )
    runtime = KafkaRuntime(client=client)
    registry.set("kafka", runtime)
    registry.mark_enabled("kafka")
    context.kafka_client = client
    return runtime

__all__ = ["ensure_kafka", "KafkaRuntime"]
