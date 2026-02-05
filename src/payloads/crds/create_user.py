from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Mapping

from src.types.crds.user_status import UserStatus


@dataclass(slots=True)
class CreateUserRequest:
    username: str
    email: str
    status: UserStatus
    display_name: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "CreateUserRequest":
        return cls(
            username="e2e_user",
            email="e2e_user@example.com",
            status=UserStatus.ACTIVE,
            display_name="E2E User",
            attributes={},
            metadata={},
        )

    def override(self, **updates: Any) -> "CreateUserRequest":
        for key in updates:
            if not hasattr(self, key):
                raise ValueError(f"Unknown payload field: {key}")
        merged = dict(updates)
        if "attributes" in updates:
            merged["attributes"] = _merge_mapping(self.attributes, updates["attributes"])
        if "metadata" in updates:
            merged["metadata"] = _merge_mapping(self.metadata, updates["metadata"])
        return replace(self, **merged)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _merge_mapping(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    result.update(override)
    return result
