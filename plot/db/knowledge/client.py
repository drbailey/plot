"""Cross-run knowledge SQLite database for patterns, decisions, and artifacts."""

import sqlite3
from pathlib import Path

from ..clients.sqlite import _SQLiteBase
from ..utils import _now
from .models import RunRow, SearchResult
from .schema import SCHEMA, SCHEMA_VERSION


class KnowledgeDB(_SQLiteBase):
    """
    SQLite-backed cross-run knowledge store.

    Stores patterns, decisions, and artifacts across story iterations so agents
    can learn from previous runs and avoid repeating mistakes.

    Usage::

        db = KnowledgeDB("/path/to/stories/knowledge.db")

        run_id = db.record_run(story="my-story", iteration=1)
        db.record_pattern(run_id=run_id, tag="api", title="Use pagination",
                          description="Always paginate large result sets")
        results = db.search("pagination", limit=10)
        db.complete_run(run_id=run_id, outcome="success")
    """

    def __init__(self, db_path: str | Path) -> None:
        super().__init__(Path(db_path))
        self._ensure_schema(SCHEMA, SCHEMA_VERSION)

    # ---------- Runs ----------

    def record_run(self, story: str, iteration: int, repo_paths: str | None = None) -> int:
        """Insert a new run record and return its id."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs (story, iteration, started_at, repo_paths) VALUES (?, ?, ?, ?)",
                (story, iteration, _now(), repo_paths),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def complete_run(self, run_id: int, outcome: str) -> None:
        """Set completed_at and outcome on a run."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET completed_at = ?, outcome = ? WHERE id = ?",
                (_now(), outcome, run_id),
            )

    def get_run(self, story: str, iteration: int) -> RunRow | None:
        """Return the run for a given story + iteration, or None if absent."""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM runs WHERE story = ? AND iteration = ? LIMIT 1",
                (story, iteration),
            )
            row = cur.fetchone()
            return _row_to_run(row) if row else None

    # ---------- Patterns ----------

    def record_pattern(
        self,
        run_id: int,
        tag: str,
        title: str,
        description: str,
        context: str | None = None,
    ) -> int:
        """
        Insert or update a pattern.

        If a row with the same tag + title already exists, increments its
        frequency and updates description/context. Otherwise inserts a new row.
        Returns the id of the affected row.
        """
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM patterns WHERE tag = ? AND title = ? LIMIT 1",
                (tag, title),
            )
            existing = cur.fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE patterns
                    SET frequency = frequency + 1,
                        description = ?,
                        context = ?,
                        recorded_at = ?
                    WHERE id = ?
                    """,
                    (description, context, _now(), existing["id"]),
                )
                return int(existing["id"])
            cur = conn.execute(
                """
                INSERT INTO patterns (run_id, tag, title, description, context, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, tag, title, description, context, _now()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    # ---------- Decisions ----------

    def record_decision(
        self,
        run_id: int,
        story: str,
        context: str,
        decision: str,
        rationale: str,
    ) -> int:
        """Insert a decision record and return its id."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO decisions (run_id, story, context, decision, rationale, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, story, context, decision, rationale, _now()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    # ---------- Artifacts ----------

    def record_artifact(
        self,
        run_id: int,
        story: str,
        iteration: int,
        artifact_type: str,
        file_path: str,
        description: str,
    ) -> int:
        """Insert an artifact record and return its id."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO artifacts
                    (run_id, story, iteration, artifact_type, file_path, description, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, story, iteration, artifact_type, file_path, description, _now()),
            )
            return cur.lastrowid  # type: ignore[return-value]

    # ---------- Search ----------

    def search(self, query_text: str, limit: int = 20) -> list[SearchResult]:
        """
        Search across patterns, decisions, and artifacts using LIKE matching.

        Matches query_text against title/description/context (patterns),
        context/decision/rationale (decisions), and description/file_path
        (artifacts). Results are merged and sorted by frequency desc,
        recorded_at desc.

        # TODO: replace LIKE with FTS5 virtual table when dataset grows
        """
        like = f"%{query_text}%"
        results: list[SearchResult] = []

        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT id, title, description, context, recorded_at, frequency
                FROM patterns
                WHERE title LIKE ? OR description LIKE ? OR context LIKE ?
                """,
                (like, like, like),
            )
            for row in cur.fetchall():
                results.append(
                    SearchResult(
                        source="patterns",
                        id=row["id"],
                        recorded_at=row["recorded_at"],
                        title=row["title"],
                        description=row["description"],
                        context=row["context"],
                        frequency=row["frequency"],
                    )
                )

            # decisions — no title column; search context, decision, rationale
            cur = conn.execute(
                """
                SELECT id, story, context, decision, rationale, recorded_at
                FROM decisions
                WHERE context LIKE ? OR decision LIKE ? OR rationale LIKE ?
                """,
                (like, like, like),
            )
            for row in cur.fetchall():
                results.append(
                    SearchResult(
                        source="decisions",
                        id=row["id"],
                        recorded_at=row["recorded_at"],
                        title=None,
                        description=row["decision"],
                        context=row["context"],
                        frequency=None,
                    )
                )

            # artifacts — no title or context columns; search description, file_path
            cur = conn.execute(
                """
                SELECT id, story, artifact_type, file_path, description, recorded_at
                FROM artifacts
                WHERE description LIKE ? OR file_path LIKE ?
                """,
                (like, like),
            )
            for row in cur.fetchall():
                results.append(
                    SearchResult(
                        source="artifacts",
                        id=row["id"],
                        recorded_at=row["recorded_at"],
                        title=row["artifact_type"],
                        description=row["description"],
                        context=None,
                        frequency=None,
                    )
                )

        results.sort(
            key=lambda r: (r.frequency or 0, r.recorded_at),
            reverse=True,
        )
        return results[:limit]

    # ---------- Raw passthrough ----------

    def execute(self, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        """
        Execute raw SQL against knowledge.db and return rows as dicts.

        Internal/debug use only. No stability guarantee on schema or output shape.
        """
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


# ---------- Row helpers ----------


def _row_to_run(row: sqlite3.Row) -> RunRow:
    return RunRow(**dict(row))
