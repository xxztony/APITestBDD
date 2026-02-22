from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from src.core.config.config import Config
from src.core.http.http_client import HttpClient
from hooks.resources.auth_resource import ensure_auth
from hooks.resources.registry import ResourceRegistry

logger = logging.getLogger(__name__)


class HttpClientFactory:
    def __init__(self, config: Config, token_manager, *, validate_schema: bool = False, timeout: float = 10.0) -> None:
        self._config = config
        self._token_manager = token_manager
        self._validate_schema = validate_schema
        self._timeout = timeout
        self._clients: dict[str, HttpClient] = {}

    def get(self, service: str) -> HttpClient:
        key = service or "default"
        if key in self._clients:
            return self._clients[key]
        base_url = self._config.get(f"{key}.http.base_url") or self._config.get("http.base_url")
        if not base_url:
            raise ValueError(f"Missing base_url for service '{key}' (expect {key}.http.base_url)")
        client = HttpClient(
            base_url=base_url,
            token_manager=self._token_manager,
            timeout=self._timeout,
            validate_schema=self._validate_schema,
        )
        self._clients[key] = client
        return client

    def close_all(self) -> None:
        for client in self._clients.values():
            session = getattr(client, "_session", None)
            if session and hasattr(session, "close"):
                try:
                    session.close()
                except Exception:  # noqa: BLE001
                    logger.warning("Failed to close HttpClient session", exc_info=True)


class ClientRegistry(dict):
    """Holds API clients keyed by name."""


@dataclass
class ApiRuntime:
    http_factory: HttpClientFactory
    clients: ClientRegistry

    def close(self) -> None:
        self.http_factory.close_all()


def _bool_from_config(config: Config, key: str, default: bool = False) -> bool:
    raw = config.get(key, default)
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(raw)


def ensure_api(context) -> ApiRuntime:
    registry: ResourceRegistry = context.resources
    if registry.has("api"):
        runtime: ApiRuntime = registry.get("api")
        registry.mark_enabled("api")
        if _has_service(context, "crds"):
            context.http_client = runtime.http_factory.get("crds")
        context.clients = runtime.clients
        context.systems = getattr(context, "systems", runtime.clients)
        return runtime

    # ensure auth dependency
    ensure_auth(context)

    config: Config = context.config_obj
    validate_schema = _bool_from_config(config, "validate_schema", False)
    http_factory = HttpClientFactory(config, context.token_manager, validate_schema=validate_schema, timeout=10.0)

    clients = ClientRegistry()
    systems: dict[str, Any] = {}

    # Register known service clients (extendable)
    if _has_service(context, "crds"):
        try:
            from src.clients.crds.user_client import CrdsUserClient
            from src.systems.crds.user import CRDSUser
        except Exception:  # noqa: BLE001
            logger.warning("CRDS client import failed; skipping registration", exc_info=True)
        else:
            crds_http = http_factory.get("crds")
            context.http_client = crds_http
            clients["crds_user"] = CrdsUserClient(crds_http)
            systems["crds_user"] = CRDSUser(context)

    runtime = ApiRuntime(http_factory=http_factory, clients=clients)
    registry.set("api", runtime)
    registry.mark_enabled("api")

    # backward compatibility
    context.clients = clients
    context.http_client_factory = http_factory
    context.systems = systems
    context.system_factories = {}
    return runtime


def _has_service(context, service: str) -> bool:
    config: Config = context.config_obj
    return bool(config.get(f"{service}.http.base_url"))

__all__ = ["ensure_api", "ApiRuntime", "HttpClientFactory", "ClientRegistry"]
