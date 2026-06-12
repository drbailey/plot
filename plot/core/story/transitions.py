"""
Transition operations: finalize, unblock, replan, skip-stage.

All functions are registered as CLI commands via @command. Importing this
module overrides the stub registrations in plot.cli.stubs for the transition
command group (finalize, unblock, replan, skip-stage).

Business logic only — no argparse, no output formatting. The CLI dispatcher
in plot.cli.builder calls output.emit_result() after a successful command.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from plot.cli.commands import Arg, command
from plot.core.base.errors import PlotError
from plot.core.base.result import Result
from plot.core.story.workflow import StoryWorkflow
from plot.db import Events, KnowledgeDB

VALID_STAGES: frozenset[str] = frozenset({
    "goal",
    "requirements",
    "architecture",
    "task_breakdown",
    "implementation",
    "verification",
    "integration",
})


@dataclass
class TransitionResult(Result):
    """Outcome of a story transition operation."""

    story: str
    action: str
    phase: str
    iteration: int
    message: str | None = None

    def __str__(self) -> str:
        lines = [
            f"Action: {self.action}",
            f"Story: {self.story} | Phase: {self.phase} | Iteration: {self.iteration}",
        ]
        if self.message:
            lines.append(f"Message: {self.message}")
        return "\n".join(lines)


@command(name="finalize", help="Complete story.", group="transition")
def finalize(
    story: str,
    message: Annotated[str | None, Arg(help="Completion message.", short="-m")] = None,
) -> TransitionResult:
    """Transition story to complete and close the knowledge run if one exists."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' not found.")
    iteration = state["current_plan"]
    wf.db.update_state(phase="complete", last_signal="WORKFLOW_COMPLETE")
    wf.logger.log(
        "INFO",
        Events.WORKFLOW_COMPLETE,
        task_id=0,
        message=message or f"Story '{story}' finalized",
    )
    kdb = KnowledgeDB(wf.stories_dir / "knowledge.db")
    run = kdb.get_run(story, iteration)
    if run is not None:
        kdb.complete_run(run.id, outcome="success")
    return TransitionResult(
        story=story,
        action="finalize",
        phase="complete",
        iteration=iteration,
        message=message,
    )


@command(name="unblock", help="Resolve a block.", group="transition")
def unblock(
    story: str,
    message: Annotated[str | None, Arg(help="Resolution summary.", short="-m")] = None,
) -> TransitionResult:
    """Transition story from blocked back to execution."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' not found.")
    iteration = state["current_plan"]
    wf.db.update_state(phase="execution", last_signal="UNBLOCKED", awaiting_human=False)
    wf.logger.log(
        "INFO",
        Events.UNBLOCKED,
        task_id=0,
        message=message or "Block resolved",
    )
    return TransitionResult(
        story=story,
        action="unblock",
        phase="execution",
        iteration=iteration,
        message=message,
    )


@command(name="replan", help="Increment iteration and return to execution.", group="transition")
def replan(
    story: str,
    message: Annotated[str | None, Arg(help="Reason for replan.", short="-m")] = None,
) -> TransitionResult:
    """Increment the plan iteration and transition directly to execution, skipping planning."""
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' not found.")
    new_iteration = state["current_plan"] + 1
    story_dir = wf.stories_dir / story / f"story{new_iteration}"
    (story_dir / "plan").mkdir(parents=True, exist_ok=True)
    wf.db.update_state(
        current_plan=new_iteration,
        phase="execution",
        last_signal="REPLAN",
        current_task=None,
        last_exec_number=0,
    )
    wf.logger.log(
        "INFO",
        Events.REPLAN,
        task_id=0,
        message=message or f"Replanned to story{new_iteration}",
    )
    return TransitionResult(
        story=story,
        action="replan",
        phase="execution",
        iteration=new_iteration,
        message=message,
    )


@command(name="skip-stage", help="Skip a stage.", group="transition")
def skip_stage(
    story: str,
    stage: str,
    message: Annotated[str, Arg(help="Skip reason (required).", short="-m")],
) -> TransitionResult:
    """Record a stage skip in the stages table. Requires -m."""
    if stage not in VALID_STAGES:
        valid = ", ".join(sorted(VALID_STAGES))
        raise PlotError(f"Invalid stage '{stage}'. Valid stages: {valid}")
    wf = StoryWorkflow(story)
    state = wf.db.get_state()
    if state is None:
        raise PlotError(f"Story '{story}' not found.")
    iteration = state["current_plan"]
    wf.db.add_stage(
        story=story,
        iteration=iteration,
        stage=stage,
        status="skipped",
        skip_reason=message,
    )
    wf.logger.log(
        "INFO",
        Events.STAGE_SKIPPED,
        task_id=0,
        message=f"Stage '{stage}' skipped: {message}",
    )
    return TransitionResult(
        story=story,
        action="skip-stage",
        phase=state["phase"],
        iteration=iteration,
        message=message,
    )
