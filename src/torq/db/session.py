"""Database connections for the work-order store.

Set ``DATABASE_URL`` to a Postgres URI for cloud persistence. When it is not
set, TORQ keeps using the local SQLite database.
"""

import re
import sqlite3
from types import TracebackType
from typing import Any, LiteralString, Self, cast

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from torq.config import settings


_REPLACE_WORK_ORDER = re.compile(r"^\s*REPLACE\s+INTO\s+work_orders\b", re.IGNORECASE)
_ROWID = re.compile(r"\browid\b", re.IGNORECASE)

_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            settings.database_url,
            min_size=0,
            max_size=10,
            max_idle=300,
            kwargs={"row_factory": cast(Any, dict_row), "prepare_threshold": None},
        )
        import atexit

        atexit.register(_pool.close)
    return _pool


def _postgres_sql(sql: str) -> str:
    """Translate the small SQLite SQL surface used by ``db.models``."""
    if _REPLACE_WORK_ORDER.match(sql):
        return (
            "INSERT INTO work_orders "
            "(id, status, machine, fault_code, assigned_to, data) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET "
            "status = EXCLUDED.status, "
            "machine = EXCLUDED.machine, "
            "fault_code = EXCLUDED.fault_code, "
            "assigned_to = EXCLUDED.assigned_to, "
            "data = EXCLUDED.data"
        )

    # Postgres uses ``%s`` parameters and has no SQLite ``rowid`` column.
    return _ROWID.sub("id", sql).replace("?", "%s")


class _PostgresConnection:
    """Borrow a connection from the pool and translate SQL for Postgres."""

    def __init__(self, pool_connection: ConnectionPool) -> None:
        self._pool_connection = pool_connection
        self._connection: psycopg.Connection[dict[str, Any]] | None = None

    def __enter__(self) -> Self:
        self._connection = cast(
            psycopg.Connection[dict[str, Any]], self._pool_connection.__enter__()
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._pool_connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> Any:
        query = cast(LiteralString, _postgres_sql(sql))
        return self._connection.execute(query, parameters)


class _SQLiteConnection:
    """Context manager wrapping a SQLite connection to ensure proper transaction commit/rollback
    and cleanup (closing the connection) on block exit. This prevents database locks on Windows.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def __enter__(self) -> sqlite3.Connection:
        self._connection.__enter__()
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            self._connection.__exit__(exc_type, exc_value, traceback)
        finally:
            self._connection.close()
        return None


def get_conn() -> _SQLiteConnection | _PostgresConnection:
    """Return a pooled Postgres connection when DATABASE_URL is set, else SQLite."""
    if settings.database_url:
        return _PostgresConnection(_get_pool().connection())

    sqlite_connection = sqlite3.connect(settings.db_path)
    sqlite_connection.row_factory = sqlite3.Row
    sqlite_connection.execute("PRAGMA journal_mode=WAL")
    sqlite_connection.execute("PRAGMA busy_timeout=5000")
    return _SQLiteConnection(sqlite_connection)
