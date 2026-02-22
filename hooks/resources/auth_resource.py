from __future__ import annotations

from dataclasses import dataclass

from src.core.security.token_manager import TokenManager
from hooks.resources.registry import ResourceRegistry


@dataclass
class AuthRuntime:
    token_manager: TokenManager

    def close(self) -> None:  # auth may not need explicit teardown
        return


def ensure_auth(context) -> AuthRuntime:
    registry: ResourceRegistry = context.resources
    if registry.has("auth"):
        registry.mark_enabled("auth")
        runtime: AuthRuntime = registry.get("auth")
        context.token_manager = runtime.token_manager
        return runtime

    token_manager = TokenManager()
    runtime = AuthRuntime(token_manager=token_manager)
    registry.set("auth", runtime)
    registry.mark_enabled("auth")
    context.token_manager = token_manager
    return runtime

__all__ = ["ensure_auth", "AuthRuntime"]
