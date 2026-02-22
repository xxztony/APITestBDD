from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """Scenario-scoped resource registry with deterministic teardown."""

    def __init__(self) -> None:
        self._resources: dict[str, Any] = {}
        self._enabled_in_scenario: set[str] = set()

    # basic ops
    def set(self, name: str, obj: Any) -> None:
        if not name:
            raise ValueError("resource name required")
        self._resources[name] = obj

    def get(self, name: str) -> Any:
        if name not in self._resources:
            raise KeyError(f"resource '{name}' not found")
        return self._resources[name]

    def has(self, name: str) -> bool:
        return name in self._resources

    def mark_enabled(self, name: str) -> None:
        self._enabled_in_scenario.add(name)

    # lifecycle
    def begin_scenario(self) -> None:
        self._enabled_in_scenario = set()

    def teardown_scenario(self) -> None:
        for name in list(self._enabled_in_scenario):
            obj = self._resources.get(name)
            self._teardown_resource(name, obj)
            self._resources.pop(name, None)
        self._enabled_in_scenario = set()

    def _teardown_resource(self, name: str, obj: Any) -> None:
        if obj is None:
            return
        close_chain: list[Callable[[], None]] = []
        for attr in ("close", "quit", "dispose"):
            fn = getattr(obj, attr, None)
            if callable(fn):
                close_chain.append(fn)
        seen = set()
        for fn in close_chain:
            if fn in seen:
                continue
            seen.add(fn)
            try:
                fn()
            except Exception:  # noqa: BLE001
                logger.warning("Failed to teardown resource '%s' via %s", name, getattr(fn, '__name__', fn), exc_info=True)

__all__ = ["ResourceRegistry"]
