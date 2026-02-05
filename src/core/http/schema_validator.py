from __future__ import annotations

from typing import Any, Callable


class SchemaValidationError(ValueError):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message)
        self.details = details


class SchemaValidator:
    @staticmethod
    def validate(data: Any, schema: Any) -> None:
        if schema is None:
            return
        if callable(schema) and not isinstance(schema, type):
            try:
                schema(data)
                return
            except Exception as exc:  # noqa: BLE001
                raise SchemaValidationError("Callable schema validation failed", details=str(exc)) from exc

        if SchemaValidator._is_pydantic_model(schema):
            SchemaValidator._validate_pydantic(data, schema)
            return

        if isinstance(schema, dict):
            SchemaValidator._validate_jsonschema(data, schema)
            return

        raise SchemaValidationError(f"Unsupported schema type: {type(schema)!r}")

    @staticmethod
    def _is_pydantic_model(schema: Any) -> bool:
        return hasattr(schema, "model_validate") or hasattr(schema, "parse_obj") or hasattr(schema, "model_dump")

    @staticmethod
    def _validate_pydantic(data: Any, schema: Any) -> None:
        try:
            target = schema if hasattr(schema, "model_validate") or hasattr(schema, "parse_obj") else schema.__class__
            if hasattr(target, "model_validate"):
                target.model_validate(data)
            elif hasattr(target, "parse_obj"):
                target.parse_obj(data)
        except Exception as exc:  # noqa: BLE001
            raise SchemaValidationError("Pydantic schema validation failed", details=str(exc)) from exc

    @staticmethod
    def _validate_jsonschema(data: Any, schema: dict[str, Any]) -> None:
        try:
            import jsonschema
        except Exception as exc:  # noqa: BLE001
            raise SchemaValidationError(
                "jsonschema is required to validate dict schemas"
            ) from exc

        try:
            jsonschema.validate(instance=data, schema=schema)
        except Exception as exc:  # noqa: BLE001
            raise SchemaValidationError("JSON schema validation failed", details=str(exc)) from exc
