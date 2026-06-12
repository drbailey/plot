"""
Task lifecycle operations.

All functions are registered as CLI commands via @command. Importing this
module populates COMMAND_REGISTRY with the task mutation commands:
log, update, task-update, start-task, complete-task, fail-task,
add-task, and verify-task.

Business logic only — no argparse, no output formatting. The CLI dispatcher
in plot.cli.builder calls output.emit_result() after a successful command.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from plot.cli.commands import Arg, command
from plot.core.base.errors import PlotError
from plot.core.config.paths import get_stories_dir
from plot.core.story.workflow import StoryWorkflow
from plot.db import Events

# ── Internal helpers ───────────────────────────────────────────────────────────


def coerce_value(s: str) -> bool | int | None | str:
    """Coerce a string value to the appropriate Python type.

    Converts "true"/"false" → bool, "null"/"none" → None,
    integers → int, everything else remains a str.
    """
    lower = s.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "none", ""):
        return None
    try:
        return int(s)
    except ValueError:
        return s


def task_slug(title: str) -> str:
    """Convert a task title to a lowercase, hyphenated slug (max 40 chars)."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:40]


def create_task_files(
    stories_dir: Path,
    story: str,
    iteration: int,
    task_id: int,
    title: str,
    slug: str,
    objective: str | None,
    criteria: str | None,
) -> tuple[Path, Path]:
    """Write task definition and work log files; create dirs if missing.

    Returns:
        (definition_path, work_log_path)
    """
    story_dir = stories_dir / story / f"story{iteration}"
    tasks_dir = story_dir / "tasks"
    work_dir = story_dir / "work"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    def_path = tasks_dir / f"task-{task_id}-{slug}.md"
    work_path = work_dir / f"task-{task_id}-work.md"

    # Task definition file (no Work Log section)
    lines = [f"# Task {task_id}: {title}", ""]
    if objective:
        lines += ["## Objective", "", objective, ""]
    if criteria:
        lines += ["## Success Criteria", "", criteria, ""]
    lines += [
        "## Scope",
        "",
        "### In Scope",
        "",
        "### Out of Scope",
        "",
        "## Approach",
        "",
        "## Notes",
        "",
    ]
    def_path.write_text("\n".join(lines), encoding="utf-8")

    # Work log file
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    work_lines = [
        f"# Work Log: Task {task_id} \u2014 {title}",
        "",
        f"Created: {now}",
        "",
        "## Work Log",
        "",
    ]
    work_path.write_text("\n".join(work_lines), encoding="utf-8")

    return def_path, work_path


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class LogResult:
    """Outcome of a log-entry operation."""

    event: str
    level: str
    task_id: int | None
    message: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "level": self.level,
            "task_id": self.task_id,
            "message": self.message,
        }

    def __str__(self) -> str:
        parts = [f"Logged {self.level} {self.event}"]
        if self.task_id is not None:
            parts.append(f"task={self.task_id}")
        if self.message:
            parts.append(f"\u2014 {self.message}")
        return " ".join(parts)


@dataclass
class StateResult:
    """Outcome of an update-state operation (shows updated key/value pairs)."""

    updated: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"updated": self.updated}

    def __str__(self) -> str:
        if not self.updated:
            return "No fields updated."
        lines = ["Updated:"]
        for key, value in self.updated.items():
            lines.append(f"  {key}: {value!r}")
        return "\n".join(lines)


@dataclass
class TaskResult:
    """Outcome of a task lifecycle operation."""

    task_id: int
    status: str
    title: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"task_id": self.task_id, "status": self.status}
        if self.title is not None:
            d["title"] = self.title
        if self.warnings:
            d["warnings"] = self.warnings
        return d

    def __str__(self) -> str:
        line = f"Task {self.task_id}: {self.status}"
        if self.title:
            line += f" ({self.title})"
        return line


# ── Commands ───────────────────────────────────────────────────────────────────


@command(name="log", help="Add a log entry.", group="task")
def log_entry(
    story: str,
    event: str,
    level: str = "INFO",
    task: int | None = None,
    message: Annotated[str | None, Arg(help="Log message.", short="-m")] = None,
) -> LogResult:
    """Append a log entry to the story event log."""
    wf = StoryWorkflow(story)
    wf.logger.log(level, event, task_id=task, message=message)
    return LogResult(event=event, level=level, task_id=task, message=message)


@command(name="update", help="Update state fields.", group="task")
def update_state(story: str, updates: list[str]) -> StateResult:
    """Update story state fields from KEY=VALUE pairs."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    coerced: dict[str, Any] = {}
    for item in updates:
        if "=" not in item:
            raise PlotError(f"Invalid KEY=VALUE pair: {item!r}")
        key, _, raw = item.partition("=")
        coerced[key.strip()] = coerce_value(raw)

    wf.db.update_state(**coerced)
    wf.logger.log("INFO", Events.STATE_UPDATE, message=f"Updated: {list(coerced.keys())}")
    return StateResult(updated=coerced)


@command(name="task-update", help="Update task fields.", group="task")
def update_task_fields(
    story: str,
    task_id: int,
    updates: list[str],
    plan: int | None = None,
) -> TaskResult:
    """Update task fields from KEY=VALUE pairs."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan_number = plan if plan is not None else state["current_plan"]
    task_row = wf.db.get_task(task_id, plan_number=plan_number)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan_number}.")

    coerced: dict[str, Any] = {}
    for item in updates:
        if "=" not in item:
            raise PlotError(f"Invalid KEY=VALUE pair: {item!r}")
        key, _, raw = item.partition("=")
        coerced[key.strip()] = coerce_value(raw)

    wf.db.update_task(task_id, plan_number=plan_number, **coerced)
    wf.logger.log(
        "INFO",
        Events.TASK_UPDATE,
        task_id=task_id,
        message=f"Updated task {task_id}: {list(coerced.keys())}",
    )
    updated_row = wf.db.get_task(task_id, plan_number=plan_number)
    status = updated_row.status if updated_row is not None else task_row.status
    return TaskResult(task_id=task_id, status=status, title=task_row.title)


@command(name="start-task", help="Start a task.", group="task")
def start_task(story: str, task_id: int) -> TaskResult:
    """Increment attempts, set task in_progress, log TASK_START."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan = state["current_plan"]
    task_row = wf.db.get_task(task_id, plan_number=plan)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan}.")

    new_attempts = task_row.attempts + 1
    wf.db.update_task(task_id, plan_number=plan, status="in_progress", attempts=new_attempts)
    wf.logger.log(
        "INFO",
        Events.TASK_START,
        task_id=task_id,
        message=f"Starting task {task_id}: {task_row.title}",
    )
    return TaskResult(task_id=task_id, status="in_progress", title=task_row.title)


@command(name="complete-task", help="Complete a task.", group="task")
def complete_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Completion message.", short="-m")] = None,
) -> TaskResult:
    """Set task completed, update last_task, log TASK_COMPLETE.

    Populates warnings if verify_status is null so the dispatcher can
    emit them to stderr.
    """
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan = state["current_plan"]
    task_row = wf.db.get_task(task_id, plan_number=plan)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan}.")

    wf.db.update_task(task_id, plan_number=plan, status="completed")
    wf.db.update_state(last_task=task_id)
    wf.logger.log(
        "INFO",
        Events.TASK_COMPLETE,
        task_id=task_id,
        message=message or f"Completed task {task_id}",
    )

    warnings: list[str] = []
    if task_row.verify_status is None:
        warnings.append(f"no verification recorded for task {task_id}")

    return TaskResult(task_id=task_id, status="completed", title=task_row.title, warnings=warnings)


@command(name="fail-task", help="Fail a task.", group="task")
def fail_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Failure reason.", short="-m")] = None,
) -> TaskResult:
    """Set task failed, log TASK_FAILED."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan = state["current_plan"]
    task_row = wf.db.get_task(task_id, plan_number=plan)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan}.")

    wf.db.update_task(task_id, plan_number=plan, status="failed")
    wf.logger.log(
        "INFO",
        Events.TASK_FAILED,
        task_id=task_id,
        message=message or f"Failed task {task_id}",
    )
    return TaskResult(task_id=task_id, status="failed", title=task_row.title)


@command(name="add-task", help="Add a task.", group="task")
def add_task(
    story: str,
    task_id: int,
    title: str,
    plan: int | None = None,
    dependencies: Annotated[str | None, Arg(help="Comma-separated task IDs.", short="-d")] = None,
    objective: Annotated[str | None, Arg(help="Task objective.", short="-o")] = None,
    success_criteria: Annotated[
        str | None, Arg(help="Success criteria.", short="-s")
    ] = None,
) -> TaskResult:
    """Create a DB entry and task files for a new task."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan_number = plan if plan is not None else state["current_plan"]

    dep_list: list[str] | None = None
    if dependencies:
        dep_list = [d.strip() for d in dependencies.split(",") if d.strip()]

    wf.db.add_task(
        task_id=task_id,
        title=title,
        plan_number=plan_number,
        dependencies=dep_list,
        objective=objective,
        success_criteria=success_criteria,
    )

    slug = task_slug(title)
    stories_dir = get_stories_dir()
    create_task_files(
        stories_dir=stories_dir,
        story=story,
        iteration=plan_number,
        task_id=task_id,
        title=title,
        slug=slug,
        objective=objective,
        criteria=success_criteria,
    )

    wf.logger.log(
        "INFO",
        Events.TASK_ADDED,
        task_id=task_id,
        message=f"Added task {task_id}: {title}",
    )
    return TaskResult(task_id=task_id, status="pending", title=title)


@command(name="verify-task", help="Verify task complete (external work).", group="task")
def verify_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Verification note.", short="-m")] = None,
) -> TaskResult:
    """Record external verification note for a task."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' has no state. Has it been initialized?")

    plan = state["current_plan"]
    task_row = wf.db.get_task(task_id, plan_number=plan)
    if task_row is None:
        raise PlotError(f"Task {task_id} not found in plan {plan}.")

    verify_msg = message or f"Verified task {task_id}"
    wf.db.update_task(task_id, plan_number=plan, verify_status=verify_msg)
    wf.logger.log(
        "INFO",
        Events.TASK_VERIFIED,
        task_id=task_id,
        message=verify_msg,
    )
    return TaskResult(task_id=task_id, status=task_row.status, title=task_row.title)
