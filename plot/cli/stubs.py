"""
Stub registrations for CLI commands that will be implemented in tasks 10-13.

Each function is decorated with @command so its signature is immediately
available to the CLI builder (and therefore to --help). When a task implements
a command, the stub body is replaced by the real core function in plot/core/,
which carries its own @command decorator.

--json is added to every subparser automatically by the builder; it does not
appear in stub signatures.
"""

from __future__ import annotations

from typing import Annotated, Literal

from plot.cli.commands import Arg, command
from plot.core.errors import PlotError

# ── Task 10: story query and routing ──────────────────────────────────────────


@command(name="next", help="Route to next action.", group="story")
def next_action(story: str) -> int:
    raise PlotError("Command not yet implemented: next")


@command(name="state", help="Show current state.", group="story")
def state(story: str) -> int:
    raise PlotError("Command not yet implemented: state")


@command(name="tasks", help="List tasks.", group="story")
def tasks(story: str, plan: int | None = None) -> int:
    raise PlotError("Command not yet implemented: tasks")


@command(name="task", help="Show task details.", group="story")
def task(story: str, task_id: int, plan: int | None = None) -> int:
    raise PlotError("Command not yet implemented: task")


@command(name="logs", help="Show log entries.", group="story")
def logs(
    story: str,
    limit: int = 20,
    event: str | None = None,
    task: int | None = None,
) -> int:
    raise PlotError("Command not yet implemented: logs")


# ── Task 11: task lifecycle ────────────────────────────────────────────────────


@command(name="log", help="Add a log entry.", group="task")
def log(
    story: str,
    event: str,
    level: str = "INFO",
    task: int | None = None,
    message: Annotated[str | None, Arg(help="Log message.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: log")


@command(name="update", help="Update state fields.", group="task")
def update(story: str, updates: list[str]) -> int:
    raise PlotError("Command not yet implemented: update")


@command(name="task-update", help="Update task fields.", group="task")
def task_update(story: str, task_id: int, updates: list[str], plan: int | None = None) -> int:
    raise PlotError("Command not yet implemented: task-update")


@command(name="start-task", help="Start a task.", group="task")
def start_task(story: str, task_id: int) -> int:
    raise PlotError("Command not yet implemented: start-task")


@command(name="complete-task", help="Complete a task.", group="task")
def complete_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Completion message.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: complete-task")


@command(name="fail-task", help="Fail a task.", group="task")
def fail_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Failure reason.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: fail-task")


@command(name="add-task", help="Add a task.", group="task")
def add_task(
    story: str,
    task_id: int,
    title: str,
    plan: int | None = None,
    dependencies: Annotated[str | None, Arg(help="Comma-separated task IDs.", short="-d")] = None,
    objective: Annotated[str | None, Arg(help="Task objective.", short="-o")] = None,
    success_criteria: Annotated[str | None, Arg(help="Success criteria.", short="-s")] = None,
) -> int:
    raise PlotError("Command not yet implemented: add-task")


@command(name="verify-task", help="Verify task complete (external work).", group="task")
def verify_task(
    story: str,
    task_id: int,
    message: Annotated[str | None, Arg(help="Verification note.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: verify-task")


# ── Task 12: transitions, meta, knowledge ─────────────────────────────────────


@command(name="finalize", help="Complete story.", group="transition")
def finalize(
    story: str,
    message: Annotated[str | None, Arg(help="Completion message.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: finalize")


@command(name="unblock", help="Resolve a block.", group="transition")
def unblock(
    story: str,
    message: Annotated[str | None, Arg(help="Resolution summary.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: unblock")


@command(name="replan", help="Increment iteration and return to execution.", group="transition")
def replan(
    story: str,
    message: Annotated[str | None, Arg(help="Reason for replan.", short="-m")] = None,
) -> int:
    raise PlotError("Command not yet implemented: replan")


@command(name="skip-stage", help="Skip a stage.", group="transition")
def skip_stage(
    story: str,
    stage: str,
    message: Annotated[str, Arg(help="Skip reason (required).", short="-m")],
) -> int:
    raise PlotError("Command not yet implemented: skip-stage")


@command(name="repo-config", help="Show repo execution config.", group="meta")
def repo_config(story: str) -> int:
    raise PlotError("Command not yet implemented: repo-config")


@command(name="skills", help="List all known skills.", group="meta")
def skills() -> int:
    raise PlotError("Command not yet implemented: skills")


# ── Task 13: verification ─────────────────────────────────────────────────────


@command(name="context", help="Generate verification context bundle.", group="verify")
def context(story: str, task_id: int) -> int:
    raise PlotError("Command not yet implemented: context")


@command(name="verify-submit", help="Submit verification result.", group="verify")
def verify_submit(
    story: str,
    task_id: int,
    outcome: Literal["pass", "fail"],
    message: Annotated[str, Arg(help="Findings (required).", short="-m")],
) -> int:
    raise PlotError("Command not yet implemented: verify-submit")
