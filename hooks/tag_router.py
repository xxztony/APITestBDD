from __future__ import annotations

from hooks.resources.api_resource import ensure_api
from hooks.resources.auth_resource import ensure_auth
from hooks.resources.ui_resource import ensure_ui
from hooks.resources.db_resource import ensure_db
from hooks.resources.kafka_resource import ensure_kafka

TAG_HANDLERS = {
    "api": ensure_api,
    "auth": ensure_auth,
    "ui": ensure_ui,
    "db": ensure_db,
    "kafka": ensure_kafka,
}


def handle_before_tag(context, tag: str) -> None:
    handler = TAG_HANDLERS.get(tag.lower())
    if handler:
        handler(context)


def handle_after_tag(context, tag: str) -> None:
    # teardown is unified in after_scenario
    return

__all__ = ["handle_before_tag", "handle_after_tag", "TAG_HANDLERS"]
