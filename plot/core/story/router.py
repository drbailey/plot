"""
Route a story to its next action based on current state.

Powers the `plot next` CLI command. Pure read logic — no side effects.
The CLI handles all state mutations based on the returned RouteResult.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from plot.db import StoryStore


class RouteAction(StrEnum):
    EXECUTE_TASK = "execute_task"
    LOOP_COMPLETE = "loop_complete"
    BLOCKED = "blocked"
    FINALIZE = "finalize"
    RESOLVE_BLOCK = "resolve_block"
    MAX_ITERATIONS = "max_iterations"
    AWAITING_HUMAN = "awaiting_human"
    ALREADY_COMPLETE = "already_complete"


@dataclass
class RouteResult:
    action: str
    task_id: int | None = None
    reason: str | None = None


def route(db: StoryStore) -> RouteResult:
    """Determine the next action for a story.

    Raises ValueError if the story is uninitialized or in planning phase.

    Possible actions:
        execute_task    - A task is ready to run
        loop_complete   - All tasks done; transition to finalize
        blocked         - No actionable tasks; needs diagnosis
        finalize        - Story is in family_finalize phase
        resolve_block   - Story is in blocked phase; needs diagnosis
        max_iterations  - Iteration limit reached
        awaiting_human  - Blocked on human intervention
        already_complete - Story is finished
    """
    state = db.get_state()
    if state is None:
        raise ValueError("No state found. Story not initialized.")

    phase = state["phase"]

    if phase == "planning":
        raise ValueError("Story is in planning phase. Use .begin to continue planning.")

    if phase == "complete":
        return RouteResult(
            action=RouteAction.ALREADY_COMPLETE,
            reason=f"Story finished on {state['updated_at']}",
        )

    if state["awaiting_human"]:
        return RouteResult(
            action=RouteAction.AWAITING_HUMAN,
            reason=state.get("awaiting_human_reason") or "Human intervention required",
        )

    if phase in ("init", "execution"):
        return _route_execution(db, state)

    if phase == "blocked":
        return RouteResult(action=RouteAction.RESOLVE_BLOCK)

    if phase == "family_finalize":
        return RouteResult(action=RouteAction.FINALIZE)

    raise ValueError(f"Unknown phase: {phase}")


def _route_execution(db: StoryStore, state: dict[str, Any]) -> RouteResult:
    """Route during the init or execution phase."""
    exec_number = state["last_exec_number"] + 1
    if exec_number > state["max_iterations"]:
        return RouteResult(
            action=RouteAction.MAX_ITERATIONS,
            reason=f"Reached {state['max_iterations']} executions",
        )

    return _find_next_task(db, state)


def _find_next_task(db: StoryStore, state: dict[str, Any]) -> RouteResult:
    """Find the next actionable task or return a terminal action."""
    plan = state["current_plan"]
    max_attempts = state["max_attempts_per_task"]
    tasks = db.get_tasks(plan_number=plan)

    if not tasks:
        return RouteResult(
            action=RouteAction.BLOCKED,
            reason=f"No tasks found in plan {plan}",
        )

    status_map = {t.task_id: t.status for t in tasks}

    if all(t.status in ("completed", "skipped") for t in tasks):
        return RouteResult(action=RouteAction.LOOP_COMPLETE)

    for task in tasks:
        if task.status in ("completed", "skipped"):
            continue
        if task.status == "failed" and task.attempts >= max_attempts:
            continue

        deps_met = all(status_map.get(d) == "completed" for d in task.dependencies)
        if not deps_met:
            continue

        return RouteResult(
            action=RouteAction.EXECUTE_TASK,
            task_id=task.task_id,
        )

    return RouteResult(
        action=RouteAction.BLOCKED,
        reason="No actionable tasks — dependencies not met or max attempts reached",
    )
