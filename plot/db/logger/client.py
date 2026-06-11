"""SQLite implementation of EventLogger: append-only workflow event log."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .._base import _now, _SQLiteBase
from .models import LogRow


class StoryLogger(_SQLiteBase):
    """
    SQLite-backed event logger targeting the logs table in a story database.

    Intentionally separate from StoryDB so the logging backend can be swapped
    (e.g. to a file, remote sink, or no-op) without touching story state or
    task management.

    Usage::

        logger = StoryLogger("/path/to/stories/my-story/story.db")
        logger.log("INFO", Events.TASK_START, task_id=1, message="Starting")
        entries = logger.get_logs(limit=20)
    """

    def __init__(self, db_path: str | Path) -> None:
        super().__init__(Path(db_path))

    def log(
        self,
        level: str,
        event: str,
        task_id: int | None = None,
        message: str | None = None,
        exec_number: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an event log entry."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO logs (timestamp, exec_number, level, event, task_id, message, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _now(),
                    exec_number,
                    level,
                    event,
                    task_id,
                    message,
                    json.dumps(details) if details else None,
                ),
            )

    def get_logs(
        self,
        limit: int = 100,
        event: str | None = None,
        task_id: int | None = None,
    ) -> list[LogRow]:
        """Return log entries (most recent first), with optional filters."""
        with self._connect() as conn:
            query = "SELECT * FROM logs"
            params: list[Any] = []
            conditions: list[str] = []

            if event:
                conditions.append("event = ?")
                params.append(event)
            if task_id:
                conditions.append("task_id = ?")
                params.append(task_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cur = conn.execute(query, params)
            return [self._row_to_log(row) for row in cur.fetchall()]

    def _row_to_log(self, row: sqlite3.Row) -> LogRow:
        data = dict(row)
        data["details"] = json.loads(data["details"]) if data["details"] else None
        return LogRow(**data)
