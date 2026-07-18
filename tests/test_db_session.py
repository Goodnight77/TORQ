"""Tests for selecting and adapting work-order database connections."""

import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from torq.config import settings
from torq.db.session import _postgres_sql, get_conn


class DatabaseSessionTests(unittest.TestCase):
    def test_sqlite_is_used_without_database_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "torq.db"
            with (
                patch.object(settings, "database_url", ""),
                patch.object(settings, "db_path", db_path),
                get_conn() as connection,
            ):
                self.assertIsInstance(connection, sqlite3.Connection)
                connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
                connection.execute("INSERT INTO sample VALUES (?)", ("local",))
                row = connection.execute("SELECT value FROM sample").fetchone()

            self.assertEqual(row["value"], "local")

    def test_postgres_connection_translates_model_sql(self) -> None:
        backend = MagicMock()
        cursor = object()
        backend.execute.return_value = cursor
        pool = MagicMock()

        @contextmanager
        def pooled_connection():
            yield backend

        pool.connection.return_value = pooled_connection()

        with (
            patch.object(settings, "database_url", "postgresql://example.invalid/torq"),
            patch("torq.db.session._get_pool", return_value=pool),
        ):
            with get_conn() as connection:
                result = connection.execute(
                    "SELECT data FROM work_orders WHERE id = ?", ("wo-1",)
                )

        pool.connection.assert_called_once_with()
        backend.execute.assert_called_once_with(
            "SELECT data FROM work_orders WHERE id = %s", ("wo-1",)
        )
        self.assertIs(result, cursor)

    def test_replace_is_translated_to_postgres_upsert(self) -> None:
        sql = _postgres_sql(
            "REPLACE INTO work_orders "
            "(id, status, machine, fault_code, assigned_to, data) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )

        self.assertTrue(sql.startswith("INSERT INTO work_orders"))
        self.assertIn("ON CONFLICT (id) DO UPDATE", sql)
        self.assertEqual(sql.count("%s"), 6)

    def test_rowid_order_uses_portable_id_column(self) -> None:
        self.assertEqual(
            _postgres_sql("SELECT data FROM work_orders ORDER BY rowid"),
            "SELECT data FROM work_orders ORDER BY id",
        )


if __name__ == "__main__":
    unittest.main()
