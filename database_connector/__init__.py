from .config import DatabaseConfig
from .connection import PostgresConnector
from .dynamodb_connection import DynamoDBConnector
from .errors import DatabaseError
from .mysql_connection import MySQLConnector


def create_connector(backend: str, config: DatabaseConfig):
    """Create the right connector for the requested backend."""
    backend_name = (backend or "postgres").lower()
    if backend_name in {"postgres", "postgresql", "pg"}:
        return PostgresConnector(config)
    if backend_name in {"mysql", "mariadb"}:
        return MySQLConnector(config)
    if backend_name in {"dynamodb", "aws-dynamodb", "dynamo"}:
        return DynamoDBConnector(config)
    raise ValueError(f"Unsupported backend: {backend}")


__all__ = [
    "DatabaseConfig",
    "PostgresConnector",
    "MySQLConnector",
    "DynamoDBConnector",
    "DatabaseError",
    "create_connector",
]
