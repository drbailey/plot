"""SQLite implementation of StoryStore: state, tasks, and stages."""

import json
import sqlite3
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any

from ..clients.sqlite import _SQLiteBase
from ..models import StageRow, TaskRow
from ..schema import STORY_DB_SCHEMA
from ..utils import _now
from .schema import SCHEMA_VERSION

_TASK_ROW_FIELDS = {f.name for f in dataclass_fields(TaskRow)}


class StoryDB(_SQLiteBase):
    """
    SQLite-backed story store.

    Manages state, tasks, and stages for a single story. Event logging is
    handled separately by StoryLogger so the two concerns can evolve or be
    replaced independently.

    Usage::

        db = StoryDB("/path/to/stories/my-story")
        db.init_state(story="my-story", repo_path="/path/to/repo", ...)

        state = db.get_state()
        db.update_state(phase="execution", last_exec_number=1)

        db.add_task(task_id=1, title="First task", ...)
        tasks = db.get_tasks(plan_number=0)

        db.add_stage(story="my-story", iteration=0, stage="plan", status="complete")
    """

    def __init__(self, family_path: str | Path) -> None:
        family = Path(family_path)
        family.mkdir(parents=True, exist_ok=True)
        super().__init__(family / "story.db")
        self.family_path = family
        self._ensure_schema(STORY_DB_SCHEMA, SCHEMA_VERSION)

    # ========== State ==========

    def init_state(
        self,
        story: str,
        repo_path: str,
        stories_dir: str,
        max_iterations: int = 20,
        max_attempts_per_task: int = 3,
        testing_available: bool | None = None,
        readme_exists: bool | None = None,
        changelog_exists: bool | None = None,
        user_context: str | None = None,
        active_stages: list[str] | None = None,
    ) -> None:
        """Initialize the state row. Call once when creating a new workflow."""
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO state (
                    id, story, repo_path, stories_dir, current_plan, phase,
                    last_exec_number, max_iterations, max_attempts_per_task,
                    last_signal, created_at, updated_at,
                    testing_available, readme_exists, changelog_exists,
                    user_context, active_stages
                ) VALUES (1, ?, ?, ?, 0, 'init', 0, ?, ?, 'INITIALIZED', ?, ?,
                    ?, ?, ?, ?, ?)
                """,
                (
                    story,
                    repo_path,
                    stories_dir,
                    max_iterations,
                    max_attempts_per_task,
                    now,
                    now,
                    1 if testing_available else 0 if testing_available is False else None,
                    1 if readme_exists else 0 if readme_exists is False else None,
                    1 if changelog_exists else 0 if changelog_exists is False else None,
                    user_context,
                    json.dumps(active_stages) if active_stages is not None else None,
                ),
            )

    def get_state(self) -> dict[str, Any] | None:
        """Return current state as a plain dict, or None if uninitialised."""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM state WHERE id = 1")
            row = cur.fetchone()
            if row is None:
                return None

            state = dict(row)
            del state["id"]

            state["awaiting_human"] = bool(state["awaiting_human"])
            for key in ("testing_available", "readme_exists", "changelog_exists"):
                if state[key] is not None:
                    state[key] = bool(state[key])

            raw = state.get("active_stages")
            state["active_stages"] = json.loads(raw) if raw else []

            return state

    def update_state(self, **kwargs: Any) -> None:
        """Update state fields. Only supplied kwargs are modified."""
        if not kwargs:
            return

        kwargs["updated_at"] = _now()

        if "awaiting_human" in kwargs:
            kwargs["awaiting_human"] = 1 if kwargs["awaiting_human"] else 0

        if "active_stages" in kwargs:
            val = kwargs["active_stages"]
            kwargs["active_stages"] = json.dumps(val) if val is not None else None

        fields = ", ".join(f"{k} = ?" for k in kwargs)
        with self._connect() as conn:
            conn.execute(  # noqa: S608
                f"UPDATE state SET {fields} WHERE id = 1",
                list(kwargs.values()),
            )

    # ========== Tasks ==========

    def add_task(
        self,
        task_id: int,
        title: str,
        plan_number: int = 0,
        dependencies: list[str] | None = None,
        objective: str | None = None,
        success_criteria: str | None = None,
        scope_in: str | None = None,
        scope_out: str | None = None,
        approach: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Insert a new task row."""
        now = _now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    task_id, plan_number, title, status, attempts, dependencies,
                    created_at, updated_at, objective, success_criteria,
                    scope_in, scope_out, approach, notes, work_log
                ) VALUES (?, ?, ?, 'pending', 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    task_id,
                    plan_number,
                    title,
                    json.dumps(dependencies or []),
                    now,
                    now,
                    objective,
                    success_criteria,
                    scope_in,
                    scope_out,
                    approach,
                    notes,
                ),
            )

    def get_task(self, task_id: int, plan_number: int = 0) -> TaskRow | None:
        """Return a single task, or None if not found."""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM tasks WHERE task_id = ? AND plan_number = ?",
                (task_id, plan_number),
            )
            row = cur.fetchone()
            return self._row_to_task(row) if row is not None else None

    def get_tasks(self, plan_number: int = 0, status: str | None = None) -> list[TaskRow]:
        """Return all tasks for a plan, optionally filtered by status."""
        with self._connect() as conn:
            if status:
                cur = conn.execute(
                    "SELECT * FROM tasks WHERE plan_number = ? AND status = ? ORDER BY task_id",
                    (plan_number, status),
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM tasks WHERE plan_number = ? ORDER BY task_id",
                    (plan_number,),
                )
            return [self._row_to_task(row) for row in cur.fetchall()]

    def update_task(self, task_id: int, plan_number: int = 0, **kwargs: Any) -> None:
        """Update task fields. Only supplied kwargs are modified."""
        if not kwargs:
            return

        kwargs["updated_at"] = _now()

        if "dependencies" in kwargs:
            kwargs["dependencies"] = json.dumps(kwargs["dependencies"])

        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [task_id, plan_number]
        with self._connect() as conn:
            conn.execute(  # noqa: S608
                f"UPDATE tasks SET {fields} WHERE task_id = ? AND plan_number = ?",
                values,
            )

    def _row_to_task(self, row: sqlite3.Row) -> TaskRow:
        data = dict(row)
        del data["id"]
        data["dependencies"] = json.loads(data["dependencies"]) if data["dependencies"] else []
        data = {k: v for k, v in data.items() if k in _TASK_ROW_FIELDS}
        return TaskRow(**data)

    # ========== Stages ==========

    def add_stage(
        self,
        story: str,
        iteration: int,
        stage: str,
        status: str,
        skip_reason: str | None = None,
        artifact_paths: str | None = None,
    ) -> None:
        """Record a new stage entry."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO stages
                    (story, iteration, stage, status, skip_reason, artifact_paths, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (story, iteration, stage, status, skip_reason, artifact_paths, _now()),
            )

    def get_stage(self, story: str, iteration: int, stage: str) -> StageRow | None:
        """Return the most recent entry for (story, iteration, stage)."""
        with self._connect() as conn:
            cur = conn.execute(
                """
                SELECT story, iteration, stage, status, skip_reason, artifact_paths, recorded_at
                FROM stages
                WHERE story = ? AND iteration = ? AND stage = ?
                ORDER BY id DESC LIMIT 1
                """,
                (story, iteration, stage),
            )
            row = cur.fetchone()
            return StageRow(**dict(row)) if row is not None else None

    def update_stage(self, story: str, iteration: int, stage: str, **kwargs: Any) -> None:
        """Update the most recent stage entry for (story, iteration, stage)."""
        if not kwargs:
            return

        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [story, iteration, stage]
        with self._connect() as conn:
            conn.execute(  # noqa: S608
                f"""
                UPDATE stages SET {fields}
                WHERE id = (
                    SELECT id FROM stages
                    WHERE story = ? AND iteration = ? AND stage = ?
                    ORDER BY id DESC LIMIT 1
                )
                """,
                values,
            )

    def get_stages(self, story: str, iteration: int | None = None) -> list[StageRow]:
        """Return all stage entries for a story, optionally filtered by iteration."""
        with self._connect() as conn:
            if iteration is not None:
                cur = conn.execute(
                    """
                    SELECT story, iteration, stage, status, skip_reason, artifact_paths, recorded_at
                    FROM stages WHERE story = ? AND iteration = ? ORDER BY id
                    """,
                    (story, iteration),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT story, iteration, stage, status, skip_reason, artifact_paths, recorded_at
                    FROM stages WHERE story = ? ORDER BY id
                    """,
                    (story,),
                )
            return [StageRow(**dict(row)) for row in cur.fetchall()]
