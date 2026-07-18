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

from torq.config import settings


_REPLACE_WORK_ORDER = re.compile(r"^\s*REPLACE\s+INTO\s+work_orders\b", re.IGNORECASE)
_ROWID = re.compile(r"\browid\b", re.IGNORECASE)


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
    """Expose the connection methods used by the unchanged model functions."""

    def __init__(self, connection: psycopg.Connection[dict[str, Any]]) -> None:
        self._connection = connection

    def __enter__(self) -> Self:
        self._connection.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> Any:
        # Model queries are application-owned SQL, never user-provided strings.
        query = cast(LiteralString, _postgres_sql(sql))
        return self._connection.execute(query, parameters)


def get_conn() -> sqlite3.Connection | _PostgresConnection:
    """Return Postgres when configured, otherwise the local SQLite database."""
    if settings.database_url:
        postgres_connection = cast(
            psycopg.Connection[dict[str, Any]],
            psycopg.connect(
                settings.database_url, row_factory=cast(Any, dict_row), prepare_threshold=None
            ),
        )
        return _PostgresConnection(postgres_connection)

    sqlite_connection = sqlite3.connect(settings.db_path)
    sqlite_connection.row_factory = sqlite3.Row
    return sqlite_connection
