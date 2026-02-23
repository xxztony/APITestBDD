from __future__ import annotations

from hooks.resources.api_resource import ensure_api
from hooks.resources.auth_resource import ensure_auth
from hooks.resources.ui_resource import ensure_ui
from hooks.resources.db_resource import ensure_db
from hooks.resources.kafka_resource import ensure_kafka

TAG_HANDLERS = {
    "api": ensure_api,
}
_resource_object_mapping = {}

def handle_before_tag(context, tag: str) -> None:
    handler = TAG_HANDLERS.get(tag.lower())
    if handler:
        handler(context)


def handle_after_tag(context, tag: str) -> None:
    # teardown is unified in after_scenario
    return

def _create_api(context):
    url = context.get("url")
    timeout = context.get("timeout", 20)
    config: Config = context.config_obj
    validate_schema = _bool_from_config(config, "validate_schema", False)

    key = f"{service}.auth.token"
    token = context.config_obj.get(key)
    if not token:
        raise ValueError(f"Missing config: {key} (set via userdata or E2E__{service.upper()}__AUTH__TOKEN)")
    context.token_manager.set_token(service, token)

    http_factory = HttpClientFactory(config, context.token_manager, validate_schema=validate_schema, timeout=10.0)

    context.http_client[] = HTTPClient
    return

