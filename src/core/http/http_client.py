from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urljoin

import requests

from .schema_validator import SchemaValidationError, SchemaValidator
from ..security.token_manager import TokenManager


logger = logging.getLogger(__name__)
try:
    import allure
    from allure_commons.types import AttachmentType

    _ALLURE_AVAILABLE = True
except Exception:  # noqa: BLE001
    allure = None
    AttachmentType = None
    _ALLURE_AVAILABLE = False


class HttpClientError(RuntimeError):
    def __init__(self, message: str, response: requests.Response | None = None) -> None:
        super().__init__(message)
        self.response = response


@dataclass(slots=True)
class HttpResponse:
    status_code: int
    headers: Mapping[str, Any]
    text: str
    json: Any | None
    raw: requests.Response


class HttpClient:
    def __init__(
        self,
        base_url: str,
        token_manager: TokenManager | None = None,
        timeout: float = 10.0,
        validate_schema: bool = False,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")
        self._base_url = base_url.rstrip("/") + "/"
        self._session = requests.Session()
        self._timeout = timeout
        self._token_manager = token_manager or TokenManager()
        self._validate_schema = validate_schema

    def request(
        self,
        method: str,
        path: str,
        *,
        service: str | None = None,
        params: Mapping[str, Any] | None = None,
        data: Any | None = None,
        json_body: Any | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
        schema: Any | None = None,
        validate_schema: bool | None = None,
    ) -> HttpResponse:
        url = urljoin(self._base_url, path.lstrip("/"))
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)
        if service:
            token = self._token_manager.get_token(service)
            if token:
                req_headers.setdefault("Authorization", f"Bearer {token}")
        effective_timeout = timeout if timeout is not None else self._timeout
        validate = self._validate_schema if validate_schema is None else validate_schema

        if _ALLURE_AVAILABLE:
            self._attach_request(
                method=method,
                url=url,
                headers=req_headers,
                params=params,
                data=data,
                json_body=json_body,
            )

        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json_body,
                headers=req_headers,
                timeout=effective_timeout,
            )
        except requests.Timeout as exc:
            logger.error("HTTP timeout", extra={"url": url, "timeout": effective_timeout})
            raise HttpClientError(f"HTTP timeout after {effective_timeout}s for {url}") from exc
        except requests.RequestException as exc:
            logger.exception("HTTP request failed", extra={"url": url})
            raise HttpClientError(f"HTTP request failed for {url}: {exc}") from exc

        response_json: Any | None = None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                response_json = None

        if validate and schema is not None:
            if response_json is None:
                body_preview = response.text[:1000]
                raise HttpClientError(
                    f"Schema validation requires JSON response, got content-type={content_type} "
                    f"status={response.status_code} body={body_preview!r}",
                    response=response,
                )
            try:
                SchemaValidator.validate(response_json, schema)
            except SchemaValidationError as exc:
                body_preview = json.dumps(response_json, ensure_ascii=False)[:2000]
                raise HttpClientError(
                    f"Schema validation failed: {exc}. status={response.status_code} body={body_preview!r}",
                    response=response,
                ) from exc

        http_response = HttpResponse(
            status_code=response.status_code,
            headers=response.headers,
            text=response.text,
            json=response_json,
            raw=response,
        )
        if _ALLURE_AVAILABLE:
            self._attach_response(http_response)
        return http_response

    @staticmethod
    def _attach_request(
        *,
        method: str,
        url: str,
        headers: Mapping[str, str] | None,
        params: Mapping[str, Any] | None,
        data: Any | None,
        json_body: Any | None,
    ) -> None:
        if not _ALLURE_AVAILABLE:
            return
        payload = {
            "method": method.upper(),
            "url": url,
            "headers": dict(headers or {}),
            "params": dict(params or {}),
            "json": json_body,
            "data": data,
        }
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            name="HTTP Request",
            attachment_type=AttachmentType.JSON,
        )

    @staticmethod
    def _attach_response(response: HttpResponse) -> None:
        if not _ALLURE_AVAILABLE:
            return
        payload = {
            "status_code": response.status_code,
            "headers": dict(response.headers or {}),
            "body": response.json if response.json is not None else response.text,
        }
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            name="HTTP Response",
            attachment_type=AttachmentType.JSON,
        )
