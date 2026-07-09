import sys
import types

import pytest

from database_connector import (
    DatabaseConfig,
    DynamoDBConnector,
    MySQLConnector,
    PostgresConnector,
    create_connector,
)


class DummyConnection:
    closed = False

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.last = (query, params)
        self._query = query
        self._params = params

    def fetchone(self):
        if "FROM users" in self._query:
            return {"id": self._params[0], "username": "user"}
        if "FROM payments" in self._query:
            return {"payment_id": self._params[0], "amount": 100}
        return {"id": 1, "name": "test"}

    def fetchall(self):
        if "FROM users" in self._query:
            return [{"id": self._params[0], "username": "user"}]
        if "FROM payments" in self._query:
            return [{"payment_id": self._params[0], "amount": 100}]
        return [{"id": 1, "name": "test"}]


def test_database_config_from_env(monkeypatch):
    monkeypatch.setenv("PG_HOST", "db.local")
    monkeypatch.setenv("PG_PORT", "5432")
    monkeypatch.setenv("PG_NAME", "demo")
    monkeypatch.setenv("PG_USER", "user")
    monkeypatch.setenv("PG_PASSWORD", "pass")

    config = DatabaseConfig.from_env()

    assert config.host == "db.local"
    assert config.port == 5432
    assert config.dbname == "demo"
    assert config.user == "user"
    assert config.password == "pass"


def test_as_connection_string():
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )

    assert "host=localhost" in config.as_connection_string()
    assert "dbname=demo" in config.as_connection_string()


def test_connect_close(monkeypatch):
    from database_connector import connection

    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )
    connector = PostgresConnector(config)

    monkeypatch.setattr(connection.psycopg, "connect", lambda dsn, autocommit, row_factory: DummyConnection())
    connector.connect()
    assert connector._connection is not None

    connector.close()
    assert connector._connection is None


def test_fetch_methods(monkeypatch):
    from database_connector import connection

    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )
    connector = PostgresConnector(config)

    dummy_conn = DummyConnection()
    dummy_conn.cursor = lambda: DummyCursor()
    monkeypatch.setattr(connection.psycopg, "connect", lambda dsn, autocommit, row_factory: dummy_conn)

    connector.connect()
    assert connector.fetch_one("SELECT 1") == {"id": 1, "name": "test"}
    assert connector.fetch_all("SELECT 1") == [{"id": 1, "name": "test"}]


def test_fetch_user_by_id(monkeypatch):
    from database_connector import connection

    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )
    connector = PostgresConnector(config)

    dummy_conn = DummyConnection()
    dummy_conn.cursor = lambda: DummyCursor()
    monkeypatch.setattr(connection.psycopg, "connect", lambda dsn, autocommit, row_factory: dummy_conn)

    connector.connect()
    assert connector.fetch_user_by_id(42) == {"id": 42, "username": "user"}


def test_fetch_payment_by_id(monkeypatch):
    from database_connector import connection

    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )
    connector = PostgresConnector(config)

    dummy_conn = DummyConnection()
    dummy_conn.cursor = lambda: DummyCursor()
    monkeypatch.setattr(connection.psycopg, "connect", lambda dsn, autocommit, row_factory: dummy_conn)

    connector.connect()
    assert connector.fetch_payment_by_id(99) == {"payment_id": 99, "amount": 100}


def test_create_connector_factory():
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        dbname="demo",
        user="user",
        password="pass",
    )

    postgres = create_connector("postgres", config)
    mysql = create_connector("mysql", config)
    dynamodb = create_connector("dynamodb", config)

    assert isinstance(postgres, PostgresConnector)
    assert isinstance(mysql, MySQLConnector)
    assert isinstance(dynamodb, DynamoDBConnector)


def test_mysql_connector_fetches_rows(monkeypatch):
    class DummyCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params):
            self.query = query
            self.params = params

        def fetchone(self):
            return {"id": self.params[0], "username": "user"}

    class DummyConnection:
        def __init__(self):
            self.cursor_obj = DummyCursor()

        def cursor(self, dictionary=True):
            return self.cursor_obj

        def commit(self):
            return None

        def rollback(self):
            return None

        def close(self):
            return None

    class DummyMysqlModule(types.ModuleType):
        def connect(self, **kwargs):
            return DummyConnection()

    monkeypatch.setitem(sys.modules, "mysql.connector", DummyMysqlModule("mysql.connector"))

    connector = MySQLConnector(DatabaseConfig(host="localhost", port=3306, dbname="demo", user="user", password="pass"))
    connector.connect()
    row = connector.fetch_user_by_id(7)

    assert row == {"id": 7, "username": "user"}


def test_dynamodb_connector_put_and_get(monkeypatch):
    class DummyClient:
        def __init__(self):
            self.last_item = None

        def put_item(self, **kwargs):
            self.last_item = kwargs
            return {"status": "ok"}

        def get_item(self, **kwargs):
            return {"Item": {"id": {"N": "1"}}}

    class DummyResource:
        def __init__(self):
            self.meta = types.SimpleNamespace(client=DummyClient())

    class DummyBoto3Module(types.ModuleType):
        def resource(self, *args, **kwargs):
            return DummyResource()

    monkeypatch.setitem(sys.modules, "boto3", DummyBoto3Module("boto3"))

    connector = DynamoDBConnector(DatabaseConfig(backend="dynamodb", region="us-east-1"))
    connector.connect()
    put_result = connector.put_item("users", {"id": {"N": "1"}})
    get_result = connector.get_item("users", {"id": {"N": "1"}})

    assert put_result == {"status": "ok"}
    assert get_result == {"Item": {"id": {"N": "1"}}}
