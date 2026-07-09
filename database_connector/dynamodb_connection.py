from __future__ import annotations

from typing import Any, Mapping, Optional

from .config import DatabaseConfig
from .errors import ConnectionError


class DynamoDBConnector:
    """Minimal DynamoDB connector for common read/write operations."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._resource = None
        self._client = None

    def __enter__(self) -> "DynamoDBConnector":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def connect(self) -> None:
        if self._resource is not None:
            return

        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError("Install boto3 to use DynamoDBConnector") from exc

        try:
            self._resource = boto3.resource(
                "dynamodb",
                region_name=self.config.region or None,
                endpoint_url=self.config.endpoint_url or None,
                aws_access_key_id=self.config.aws_access_key_id or None,
                aws_secret_access_key=self.config.aws_secret_access_key or None,
                aws_session_token=self.config.aws_session_token or None,
            )
            self._client = self._resource.meta.client
        except Exception as exc:  # pragma: no cover - depends on AWS runtime
            raise ConnectionError("Failed to connect to DynamoDB") from exc

    def close(self) -> None:
        self._resource = None
        self._client = None

    def put_item(self, table_name: str, item: Mapping[str, Any]) -> Mapping[str, Any]:
        self._ensure_connection()
        return self._client.put_item(TableName=table_name, Item=item)

    def get_item(self, table_name: str, key: Mapping[str, Any]) -> Mapping[str, Any]:
        self._ensure_connection()
        return self._client.get_item(TableName=table_name, Key=key)

    def scan(self, table_name: str, **kwargs: Any) -> Mapping[str, Any]:
        self._ensure_connection()
        return self._client.scan(TableName=table_name, **kwargs)

    def query(self, table_name: str, **kwargs: Any) -> Mapping[str, Any]:
        self._ensure_connection()
        return self._client.query(TableName=table_name, **kwargs)

    def _ensure_connection(self) -> None:
        if self._client is None:
            raise ConnectionError("DynamoDB connection is not open")
