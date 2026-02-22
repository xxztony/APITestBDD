from __future__ import annotations

import copy
from typing import Any, Mapping


class ScenarioData:
    """Lightweight helper over shared_data dict for API-first usage (api-only layout)."""

    TEMPLATE = {
        "api": {
            "responses": {},
            "requests": {},
            "entities": {},
            "vars": {},
            "artifacts": {},
            "pages": {},
        },
    }

    def __init__(self, context: Any, shared_data: dict[str, Any] | None = None) -> None:
        self.context = context
        self.raw: dict[str, Any] = copy.deepcopy(shared_data) if shared_data is not None else copy.deepcopy(self.TEMPLATE)
        self.raw.setdefault("api", {})
        api = self.raw["api"]
        api.setdefault("responses", {})
        api.setdefault("requests", {})
        api.setdefault("entities", {})
        api.setdefault("vars", {})
        api.setdefault("artifacts", {})
        api.setdefault("pages", {})

    # ---------- API responses ----------
    def put_response(self, alias: str, response: Any, *, overwrite: bool = False) -> None:
        if not alias:
            raise ValueError("Response alias must be non-empty")
        responses = self.raw["api"]["responses"]
        if alias in responses and not overwrite:
            existing = ", ".join(sorted(responses.keys()))
            raise ValueError(f"Response alias '{alias}' already exists. Existing: [{existing}]")
        responses[alias] = response

    def get_response(self, alias: str = "last") -> Any:
        responses = self.raw["api"].get("responses") or {}
        if alias in responses:
            return responses[alias]
        available = ", ".join(sorted(responses.keys())) if responses else "<none>"
        raise KeyError(f"Response alias '{alias}' not found. Available: [{available}]")

    # ---------- Common entities ----------
    def put_entity(self, alias: str, value: Any, *, overwrite: bool = True) -> None:
        if not alias:
            raise ValueError("Entity alias must be non-empty")
        entities = self.raw["api"]["entities"]
        if alias in entities and not overwrite:
            existing = ", ".join(sorted(entities.keys()))
            raise ValueError(f"Entity alias '{alias}' already exists. Existing: [{existing}]")
        entities[alias] = value

    def get_entity(self, alias: str) -> Any:
        entities = self.raw["api"].get("entities") or {}
        if alias in entities:
            return entities[alias]
        available = ", ".join(sorted(entities.keys())) if entities else "<none>"
        raise KeyError(f"Entity alias '{alias}' not found. Available: [{available}]")

    # ---------- Common vars (string-like) ----------
    def put_var(self, alias: str, value: Any, *, overwrite: bool = True) -> None:
        if not alias:
            raise ValueError("Var alias must be non-empty")
        vars_map = self.raw["api"]["vars"]
        if alias in vars_map and not overwrite:
            existing = ", ".join(sorted(vars_map.keys()))
            raise ValueError(f"Var alias '{alias}' already exists. Existing: [{existing}]")
        vars_map[alias] = str(value) if value is not None else ""

    def get_var(self, alias: str) -> str:
        vars_map = self.raw["api"].get("vars") or {}
        if alias in vars_map:
            return vars_map[alias]
        available = ", ".join(sorted(vars_map.keys())) if vars_map else "<none>"
        raise KeyError(f"Var alias '{alias}' not found. Available: [{available}]")

    # ---------- Placeholder resolution ----------
    def resolve_placeholders(self, text: Any) -> Any:
        if not isinstance(text, str):
            return text

        def replace(match):
            name = match.group(1)
            if name in self.raw["api"]["entities"]:
                return str(self.raw["api"]["entities"][name])
            if name in self.raw["api"]["vars"]:
                return str(self.raw["api"]["vars"][name])
            available = list(self.raw["api"]["entities"].keys()) + list(self.raw["api"]["vars"].keys())
            raise KeyError(f"Placeholder '{name}' not found. Available: {sorted(available)}")

        import re

        pattern = re.compile(r"\{([^{}]+)\}")
        return pattern.sub(replace, text)

    # ---------- UI artifacts ----------
    def put_ui_artifact(self, alias: str, value: Any, *, overwrite: bool = True) -> None:
        if not alias:
            raise ValueError("UI artifact alias must be non-empty")
        if isinstance(value, (Mapping, str)):
            pass
        elif hasattr(value, "quit") or hasattr(value, "close"):
            raise ValueError("Driver/session objects are not allowed in shared_data.ui.artifacts")
        else:
            raise ValueError("UI artifacts must be a string or lightweight mapping")
        artifacts = self.raw["api"]["artifacts"]
        if alias in artifacts and not overwrite:
            existing = ", ".join(sorted(artifacts.keys()))
            raise ValueError(f"UI artifact alias '{alias}' already exists. Existing: [{existing}]")
        artifacts[alias] = value

    def get_ui_artifact(self, alias: str) -> Any:
        artifacts = self.raw["api"].get("artifacts") or {}
        if alias in artifacts:
            return artifacts[alias]
        available = ", ".join(sorted(artifacts.keys())) if artifacts else "<none>"
        raise KeyError(f"UI artifact alias '{alias}' not found. Available: [{available}]")

    # ---------- helpers ----------
    @property
    def api_state(self) -> dict[str, Any]:
        return self.raw["api"]

    def get_request_context(self) -> dict[str, Any]:
        requests = self.raw["api"].setdefault("requests", {})
        ctx = requests.setdefault("_current", {"headers": {}, "params": {}, "json": {}})
        ctx.setdefault("headers", {})
        ctx.setdefault("params", {})
        ctx.setdefault("json", {})
        return ctx
