from __future__ import annotations

import threading
from typing import Any


class TokenManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tokens: dict[str, str] = {}

    def get_token(self, service: str) -> str | None:
        if not service:
            return None
        key = service.strip()
        with self._lock:
            return self._tokens.get(key)

    def set_token(self, service: str, token: str | None) -> None:
        if not service:
            raise ValueError("service is required")
        key = service.strip()
        with self._lock:
            if token:
                self._tokens[key] = token
            else:
                self._tokens.pop(key, None)

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return dict(self._tokens)
