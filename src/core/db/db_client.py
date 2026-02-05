from __future__ import annotations

import logging
from typing import Any, Iterable, Mapping

import pyodbc


logger = logging.getLogger(__name__)


class DbClientError(RuntimeError):
    pass


class DbClient:
    def __init__(
        self,
        connection_string: str,
        *,
        timeout: int = 10,
        autocommit: bool = False,
    ) -> None:
        if not connection_string:
            raise ValueError("connection_string is required")
        self._connection_string = connection_string
        self._timeout = timeout
        try:
            self._conn = pyodbc.connect(connection_string, timeout=timeout, autocommit=autocommit)
        except Exception as exc:  # noqa: BLE001
            raise DbClientError(f"DB connection failed: {exc}") from exc

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            logger.exception("DB close failed")

    def select_one(self, query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
        rows = self.select_many(query, params=params)
        return rows[0] if rows else None

    def select_many(self, query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
        cursor = self._cursor()
        try:
            cursor.execute(query, params or [])
            columns = [col[0] for col in cursor.description] if cursor.description else []
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return result
        except Exception as exc:  # noqa: BLE001
            raise DbClientError(f"DB query failed: {exc}") from exc
        finally:
            cursor.close()

    def execute(self, query: str, params: Iterable[Any] | None = None) -> int:
        cursor = self._cursor()
        try:
            cursor.execute(query, params or [])
            return cursor.rowcount
        except Exception as exc:  # noqa: BLE001
            raise DbClientError(f"DB execute failed: {exc}") from exc
        finally:
            cursor.close()

    def _cursor(self) -> pyodbc.Cursor:
        cursor = self._conn.cursor()
        try:
            cursor.timeout = self._timeout
        except Exception:
            logger.debug("pyodbc cursor timeout not supported")
        return cursor
