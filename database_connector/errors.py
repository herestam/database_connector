class DatabaseError(Exception):
    """Base exception for PostgreSQL connector errors."""


class ConnectionError(DatabaseError):
    """Raised when the database connection cannot be established."""


class QueryError(DatabaseError):
    """Raised when a SQL query fails."""
