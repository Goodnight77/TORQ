"""SQLite connection for the local work-order store.

SQLite keeps this zero-infra; swap to Postgres via DATABASE_URL when
multi-user/persistence needs it.
"""

import sqlite3

from torq.config import settings


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn
