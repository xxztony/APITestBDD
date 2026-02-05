from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Mapping


_ENV_KEYS = ("ENV", "BEHAVE_ENV")
_ENV_PREFIX = "E2E__"
_VALID_ENVS = ("dev", "staging", "prod")


def _to_nested_dict(env_items: Mapping[str, str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw_key, value in env_items.items():
        if not raw_key.startswith(_ENV_PREFIX):
            continue
        path = raw_key[len(_ENV_PREFIX) :].lower().split("__")
        if not path:
            continue
        cursor: dict[str, Any] = data
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = value
    return data


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)  # type: ignore[arg-type]
        else:
            base[key] = value
    return base


@dataclass(frozen=True)
class Config:
    env: str
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, userdata: Mapping[str, Any] | None = None) -> "Config":
        userdata = userdata or {}
        env = (
            str(userdata.get("env") or "").strip()
            or next((os.getenv(k, "").strip() for k in _ENV_KEYS if os.getenv(k)), "")
            or "dev"
        ).lower()
        if env not in _VALID_ENVS:
            raise ValueError(f"Unsupported env '{env}', must be one of {_VALID_ENVS}")

        data: dict[str, Any] = {}
        env_block = userdata.get(env)
        if isinstance(env_block, Mapping):
            _deep_merge(data, env_block)
        _deep_merge(data, _to_nested_dict(os.environ))
        return cls(env=env, data=data)

    def get(self, key: str, default: Any | None = None) -> Any:
        if not key:
            return default
        cursor: Any = self.data
        for part in key.split("."):
            if not isinstance(cursor, Mapping) or part not in cursor:
                return default
            cursor = cursor[part]
        return cursor

    def section(self, name: str) -> dict[str, Any]:
        value = self.get(name, {})
        return dict(value) if isinstance(value, Mapping) else {}
