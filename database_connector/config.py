from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    backend: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    dbname: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    sslmode: str = "prefer"
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    @classmethod
    def from_env(cls, prefix: str = "DB") -> "DatabaseConfig":
        def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
            return os.getenv(f"{prefix}_{name}", os.getenv(f"PG_{name}", default))

        return cls(
            backend=get_env("BACKEND", "postgres").lower(),
            host=get_env("HOST", "localhost"),
            port=int(get_env("PORT", "5432")),
            dbname=get_env("NAME"),
            user=get_env("USER"),
            password=get_env("PASSWORD"),
            sslmode=get_env("SSLMODE", "prefer"),
            region=get_env("REGION"),
            endpoint_url=get_env("ENDPOINT_URL"),
            aws_access_key_id=get_env("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_env("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=get_env("AWS_SESSION_TOKEN"),
        )

    def as_connection_string(self) -> str:
        if not self.dbname or not self.user or self.password is None:
            raise ValueError("DatabaseConfig requires dbname, user, and password")

        return (
            f"host={self.host} port={self.port} dbname={self.dbname} "
            f"user={self.user} password={self.password} sslmode={self.sslmode}"
        )
