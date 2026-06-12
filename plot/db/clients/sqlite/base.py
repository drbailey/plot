"""Shared SQLite connection infrastructure for db package internals."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


class _SQLiteBase:
    """Base class providing a managed SQLite connection and schema bootstrap."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self, schema: str, version: int) -> None:
        """Create all tables defined in *schema* and stamp the schema version."""
        with self._connect() as conn:
            conn.executescript(schema)
            cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
            if cur.fetchone() is None:
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (version,),
                )
