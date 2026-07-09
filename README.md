# Postgres Connector

A lightweight reusable Python library for connecting to PostgreSQL and executing queries.

## Install

```bash
pip install psycopg[binary]
```

**Note:** This package is designed as a reusable library. Copy the `database_connector` package folder into your repository or install it with `pip` after adding proper packaging metadata.

## Usage

```python
from database_connector import DatabaseConfig, PostgresConnector

config = DatabaseConfig(
    host="localhost",
    port=5432,
    dbname="my_database",
    user="my_user",
    password="secret",
)

with PostgresConnector(config) as db:
    rows = db.fetch_all("SELECT id, name FROM users WHERE active = %s", (True,))
    print(rows)
```

## Environment configuration

Use environment variables to create a config automatically:

```python
from database_connector import PostgresConnector
from database_connector.config import DatabaseConfig

config = DatabaseConfig.from_env(prefix="PG")

with PostgresConnector(config) as db:
    print(db.fetch_one("SELECT version()"))
```

Supported environment variables:

- `PG_HOST`
- `PG_PORT`
- `PG_NAME`
- `PG_USER`
- `PG_PASSWORD`
- `PG_SSLMODE`
