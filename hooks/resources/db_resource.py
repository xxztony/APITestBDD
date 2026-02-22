from __future__ import annotations

import logging
from dataclasses import dataclass

from hooks.resources.registry import ResourceRegistry

logger = logging.getLogger(__name__)

try:
    from src.core.db.db_client import DbClient  # type: ignore
except Exception:  # noqa: BLE001
    DbClient = None  # type: ignore


@dataclass
class DbRuntime:
    client: any

    def close(self) -> None:
        if self.client and hasattr(self.client, "close"):
            self.client.close()


def ensure_db(context) -> DbRuntime:
    registry: ResourceRegistry = context.resources
    if registry.has("db"):
        runtime: DbRuntime = registry.get("db")
        registry.mark_enabled("db")
        context.db_client = runtime.client
        return runtime

    if DbClient is None:
        raise RuntimeError("DbClient implementation not available; cannot enable @db")

    conn_str = context.config_obj.get("db.connection_string") or context.config_obj.get("crds.db.connection_string")
    if not conn_str:
        raise ValueError("Missing DB connection string (db.connection_string or crds.db.connection_string)")

    client = DbClient(conn_str, timeout=10)
    runtime = DbRuntime(client=client)
    registry.set("db", runtime)
    registry.mark_enabled("db")
    context.db_client = client
    return runtime

__all__ = ["ensure_db", "DbRuntime"]
