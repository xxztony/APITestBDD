from __future__ import annotations

from typing import Any, Mapping

from src.core.http.http_client import HttpClient, HttpResponse
from src.payloads.crds.create_user import CreateUserRequest


class CrdsUserClient:
    def __init__(
        self,
        http_client: HttpClient,
        *,
        service: str = "crds",
        base_path: str = "/users",
    ) -> None:
        if not base_path:
            raise ValueError("base_path is required")
        self._http_client = http_client
        self._service = service
        self._base_path = base_path.rstrip("/")

    def create_user(
        self,
        payload: CreateUserRequest | Mapping[str, Any],
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        schema: Any | None = None,
        validate_schema: bool | None = None,
    ) -> HttpResponse:
        if not isinstance(payload, CreateUserRequest):
            payload = CreateUserRequest.default().override(**dict(payload))
        return self._http_client.request(
            method="POST",
            path=self._base_path,
            service=self._service,
            json_body=payload.to_dict(),
            headers=headers,
            timeout=timeout,
            schema=schema,
            validate_schema=validate_schema,
        )

    def get_user(
        self,
        user_id: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        schema: Any | None = None,
        validate_schema: bool | None = None,
    ) -> HttpResponse:
        return self._http_client.request(
            method="GET",
            path=f"{self._base_path}/{user_id}",
            service=self._service,
            headers=headers,
            timeout=timeout,
            schema=schema,
            validate_schema=validate_schema,
        )

    def delete_user(
        self,
        user_id: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        schema: Any | None = None,
        validate_schema: bool | None = None,
    ) -> HttpResponse:
        return self._http_client.request(
            method="DELETE",
            path=f"{self._base_path}/{user_id}",
            service=self._service,
            headers=headers,
            timeout=timeout,
            schema=schema,
            validate_schema=validate_schema,
        )
