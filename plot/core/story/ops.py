"""
Story query and routing operations.

All functions are registered as CLI commands via @command. Importing this
module overrides the stub registrations in plot.cli.stubs for the task-10
command group (next, state, tasks, task, logs).

Business logic only — no argparse, no output formatting. The CLI dispatcher
in plot.cli.builder calls output.emit_result() after a successful command.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from plot.cli.commands import command
from plot.core.base.errors import PlotError
from plot.core.base.result import Result
from plot.core.config.paths import get_stories_dir
from plot.core.story.router import RouteAction, route
from plot.db import Events, LogRow, StoryDB, StoryLogger, TaskRow

# ── Internal helpers ───────────────────────────────────────────────────────────


def _open_db(story: str) -> StoryDB:
    """Return a StoryDB for the given story name using the configured stories dir."""
    stories_dir = get_stories_dir()
    story_path = stories_dir / story
    return StoryDB(story_path)


def find_work_file(stories_dir: Path, story: str, iteration: int, task_id: int) -> Path | None:
    """Return the task spec file for task_id in story{iteration}/tasks/, or None."""
    task_dir = stories_dir / story / f"story{iteration}" / "tasks"
    matches = sorted(task_dir.glob(f"task-{task_id}-*.md"))
    return matches[0] if matches else None


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class NextResult(Result):
    """Outcome of a next-action routing operation."""

    action: str
    task_id: int | None = None
    title: str | None = None
    attempt: int | None = None
    exec_number: int | None = None
    work_file: str | None = None
    user_context: str | None = None
    reason: str | None = None

    def __str__(self) -> str:
        lines = [f"ACTION: {self.action}"]
        if self.action == RouteAction.EXECUTE_TASK:
            lines.append(
                f"Task: {self.task_id} | Attempt: {self.attempt} | Exec: {self.exec_number}"
            )
            if self.title:
                lines.append(f"Title: {self.title}")
            if self.work_file:
                lines.append(f"Work file: {self.work_file}")
            if self.user_context:
                lines.append(f"User context: {self.user_context}")
        elif self.reason:
            lines.append(f"Reason: {self.reason}")
        return "\n".join(lines)


@dataclass
class StateResult:
    """All state fields for a story."""

    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.fields)

    def __str__(self) -> str:
        return "\n".join(f"{key}: {value}" for key, value in self.fields.items())


@dataclass
class TasksResult:
    """Task list for a plan."""

    tasks: list[TaskRow] = field(default_factory=list)
    plan_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan_number,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "title": t.title,
                    "status": t.status,
                    "attempts": t.attempts,
                    "dependencies": t.dependencies,
                }
                for t in self.tasks
            ],
        }

    def __str__(self) -> str:
        if not self.tasks:
            return f"No tasks in plan {self.plan_number}."
        lines = [f"Plan {self.plan_number} — {len(self.tasks)} task(s):"]
        for t in self.tasks:
            deps = ", ".join(str(d) for d in t.dependencies) if t.dependencies else "—"
            lines.append(
                f"  [{t.task_id:>3}] {t.status:<12} att={t.attempts}"
                f"  deps={deps}  {t.title}"
            )
        return "\n".join(lines)


@dataclass
class TaskResult(Result):
    """Full details for a single task."""

    task: TaskRow
    plan_number: int = 0

    def __str__(self) -> str:
        t = self.task
        deps = ", ".join(str(d) for d in t.dependencies) if t.dependencies else "none"
        lines = [
            f"Task {t.task_id} (plan {self.plan_number}): {t.title}",
            f"  Status: {t.status}  Attempts: {t.attempts}  Dependencies: {deps}",
        ]
        if t.objective:
            lines.append(f"  Objective: {t.objective}")
        if t.success_criteria:
            lines.append(f"  Success criteria: {t.success_criteria}")
        if t.scope_in:
            lines.append(f"  Scope in: {t.scope_in}")
        if t.scope_out:
            lines.append(f"  Scope out: {t.scope_out}")
        if t.approach:
            lines.append(f"  Approach: {t.approach}")
        if t.notes:
            lines.append(f"  Notes: {t.notes}")
        if t.verify_status:
            lines.append(f"  Verify status: {t.verify_status}")
        lines.append(f"  Created: {t.created_at}  Updated: {t.updated_at}")
        return "\n".join(lines)


@dataclass
class LogsResult(Result):
    """A list of event log entries."""

    entries: list[LogRow] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.entries:
            return "No log entries."
        lines = []
        for e in self.entries:
            task_part = f" task={e.task_id}" if e.task_id is not None else ""
            exec_part = f" exec={e.exec_number}" if e.exec_number is not None else ""
            msg_part = f" — {e.message}" if e.message else ""
            lines.append(
                f"{e.timestamp} [{e.level}] {e.event}{task_part}{exec_part}{msg_part}"
            )
        return "\n".join(lines)


# ── Commands ───────────────────────────────────────────────────────────────────


@command(name="next", help="Route to next action.", group="story")
def next_action(story: str) -> NextResult:
    """Determine and execute the next action for a story.

    Auto-transitions init → execution when action is execute_task.
    Marks the selected task in_progress and increments last_exec_number.
    """
    db = _open_db(story)
    logger = StoryLogger(db.family_path / "story.db")

    try:
        route_result = route(db)
    except ValueError as exc:
        raise PlotError(str(exc)) from exc

    state = db.get_state()
    assert state is not None

    action = route_result.action
    task_id = route_result.task_id
    title: str | None = None
    attempt: int | None = None
    exec_number: int | None = None
    work_file: str | None = None

    if action == RouteAction.EXECUTE_TASK and task_id is not None:
        if state["phase"] == "init":
            db.update_state(phase="execution")

        exec_number = state["last_exec_number"] + 1
        db.update_state(last_exec_number=exec_number, current_task=task_id)

        plan = state["current_plan"]
        task_row = db.get_task(task_id, plan_number=plan)
        if task_row is not None:
            title = task_row.title
            attempt = task_row.attempts + 1
            db.update_task(task_id, plan_number=plan, status="in_progress", attempts=attempt)

        stories_dir = get_stories_dir()
        work_path = find_work_file(stories_dir, story, plan, task_id)
        work_file = str(work_path) if work_path is not None else None

        logger.log(
            "INFO",
            Events.TASK_START,
            task_id=task_id,
            exec_number=exec_number,
            message=f"Starting task {task_id}: {title}",
        )

    return NextResult(
        action=action,
        task_id=task_id,
        title=title,
        attempt=attempt,
        exec_number=exec_number,
        work_file=work_file,
        user_context=state.get("user_context"),
        reason=route_result.reason,
    )


@command(name="state", help="Show current state.", group="story")
def query_state(story: str) -> StateResult:
    """Return all state fields for a story."""
    db = _open_db(story)
    state = db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")
    return StateResult(fields=state)


@command(name="tasks", help="List tasks.", group="story")
def query_tasks(story: str, plan: int | None = None) -> TasksResult:
    """Return the task list for a plan (defaults to current plan)."""
    db = _open_db(story)
    state = db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")
    plan_number = plan if plan is not None else state["current_plan"]
    tasks = db.get_tasks(plan_number=plan_number)
    return TasksResult(tasks=tasks, plan_number=plan_number)


@command(name="task", help="Show task details.", group="story")
def query_task(story: str, task_id: int, plan: int | None = None) -> TaskResult:
    """Return full details for a single task."""
    db = _open_db(story)
    state = db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")
    plan_number = plan if plan is not None else state["current_plan"]
    task_row = db.get_task(task_id, plan_number=plan_number)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan_number}.")
    return TaskResult(task=task_row, plan_number=plan_number)


@command(name="logs", help="Show log entries.", group="story")
def query_logs(
    story: str,
    limit: int = 20,
    event: str | None = None,
    task: int | None = None,
) -> LogsResult:
    """Return event log entries for a story, with optional filters."""
    db = _open_db(story)
    logger = StoryLogger(db.family_path / "story.db")
    entries = logger.get_logs(limit=limit, event=event, task_id=task)
    return LogsResult(entries=entries)
