from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence

import psycopg
from psycopg import Connection
from psycopg.errors import DatabaseError as PsycopgDatabaseError

from .config import DatabaseConfig
from .errors import ConnectionError, DatabaseError, QueryError


class PostgresConnector:
    """Manages a PostgreSQL connection and query execution."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection: Optional[Connection] = None

    def __enter__(self) -> "PostgresConnector":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def connect(self) -> None:
        if self._connection is not None and not self._connection.closed:
            return

        try:
            self._connection = psycopg.connect(
                self.config.as_connection_string(),
                autocommit=False,
                row_factory=psycopg.rows.dict_row,
            )
        except PsycopgDatabaseError as exc:
            raise ConnectionError("Failed to connect to PostgreSQL") from exc

    def close(self) -> None:
        if self._connection is None:
            return

        try:
            self._connection.close()
        finally:
            self._connection = None

    def execute(self, query: str, params: Optional[Sequence[Any]] = None) -> None:
        self._ensure_connection()
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                self._connection.commit()
        except PsycopgDatabaseError as exc:
            self._connection.rollback()
            raise QueryError("Query execution failed") from exc

    def execute_many(self, query: str, values: Iterable[Sequence[Any]]) -> None:
        self._ensure_connection()
        try:
            with self._connection.cursor() as cursor:
                cursor.executemany(query, values)
                self._connection.commit()
        except PsycopgDatabaseError as exc:
            self._connection.rollback()
            raise QueryError("Batch execution failed") from exc

    def fetch_one(self, query: str, params: Optional[Sequence[Any]] = None) -> Mapping[str, Any]:
        self._ensure_connection()
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone() or {}
        except PsycopgDatabaseError as exc:
            raise QueryError("Failed to fetch one row") from exc

    def fetch_all(self, query: str, params: Optional[Sequence[Any]] = None) -> list[Mapping[str, Any]]:
        self._ensure_connection()
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except PsycopgDatabaseError as exc:
            raise QueryError("Failed to fetch rows") from exc

    def fetch_user_by_id(self, user_id: int, table: str = "users") -> Mapping[str, Any]:
        """Fetch a user row by its ID from the specified table."""
        query = f"SELECT * FROM {table} WHERE id = %s"
        return self.fetch_one(query, (user_id,))

    def fetch_payment_by_id(self, payment_id: int, table: str = "payments") -> Mapping[str, Any]:
        """Fetch a payment row by its payment ID from the specified table."""
        query = f"SELECT * FROM {table} WHERE payment_id = %s"
        return self.fetch_one(query, (payment_id,))

    def _ensure_connection(self) -> None:
        if self._connection is None or self._connection.closed:
            raise ConnectionError("Database connection is not open")
