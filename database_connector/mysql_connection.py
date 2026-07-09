from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from .config import DatabaseConfig
from .errors import ConnectionError, QueryError


class MySQLConnector:
    """Simple MySQL connector for executing queries and fetching rows."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None

    def __enter__(self) -> "MySQLConnector":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def connect(self) -> None:
        if self._connection is not None:
            return

        try:
            import mysql.connector as mysql_connector
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError("Install mysql-connector-python to use MySQLConnector") from exc

        try:
            self._connection = mysql_connector.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.dbname,
                user=self.config.user,
                password=self.config.password,
                autocommit=False,
            )
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise ConnectionError("Failed to connect to MySQL") from exc

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
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            self._connection.rollback()
            raise QueryError("MySQL query execution failed") from exc

    def fetch_one(self, query: str, params: Optional[Sequence[Any]] = None) -> Mapping[str, Any]:
        self._ensure_connection()
        try:
            with self._connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone() or {}
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise QueryError("MySQL fetch_one failed") from exc

    def fetch_all(self, query: str, params: Optional[Sequence[Any]] = None) -> list[Mapping[str, Any]]:
        self._ensure_connection()
        try:
            with self._connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall() or []
        except Exception as exc:  # pragma: no cover - depends on DB runtime
            raise QueryError("MySQL fetch_all failed") from exc

    def fetch_user_by_id(self, user_id: int, table: str = "users") -> Mapping[str, Any]:
        query = f"SELECT * FROM {table} WHERE id = %s"
        return self.fetch_one(query, (user_id,))

    def fetch_payment_by_id(self, payment_id: int, table: str = "payments") -> Mapping[str, Any]:
        query = f"SELECT * FROM {table} WHERE payment_id = %s"
        return self.fetch_one(query, (payment_id,))

    def _ensure_connection(self) -> None:
        if self._connection is None:
            raise ConnectionError("MySQL connection is not open")
