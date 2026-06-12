"""
Verification context and submission commands.

Implements ``plot context`` (generates verifier bundle) and ``plot verify-submit``
(records verification result). Both commands are registered via @command.

Business logic only — no argparse, no output formatting. The CLI dispatcher
in plot.cli.builder calls output.emit_result() after a successful command.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from plot.cli.commands import Arg, command
from plot.core.base.errors import WorkflowError
from plot.core.config.paths import get_stories_dir
from plot.db import Events, StoryDB, StoryLogger

# ── Internal helpers ───────────────────────────────────────────────────────────

_VERIFICATION_GUIDELINES = """\
- Requirement coverage: does the implementation address all stated criteria?
- Edge cases: are boundary conditions and unexpected inputs handled?
- Error paths: are failures handled gracefully with appropriate messaging?
- Test completeness: are tests present and meaningful for the stated criteria?\
"""


@dataclass
class ContextBundle:
    """Structured data assembled for a verifier context file."""

    task_id: int
    story: str
    iteration: int
    generated_at: str
    title: str
    objective: str | None
    success_criteria: str | None
    scope_in: str | None
    scope_out: str | None
    plan_context: str | None


def build_context_bundle(
    db: StoryDB,
    stories_dir: Path,
    story: str,
    task_id: int,
) -> ContextBundle:
    """Assemble structured context from the DB and optional plan file.

    Reads task fields from the DB record and architecture context from plan.md
    when present. Does not read the work log.
    """
    state = db.get_state()
    if state is None:
        raise WorkflowError(f"Story '{story}' has no state. Has it been initialized?")

    iteration: int = state["current_plan"]
    task_row = db.get_task(task_id, plan_number=iteration)
    if task_row is None:
        raise WorkflowError(f"Task {task_id} not found in plan {iteration}.")

    plan_file = stories_dir / story / f"story{iteration}" / "plan" / "plan.md"
    plan_context: str | None = None
    if plan_file.exists():
        plan_context = plan_file.read_text(encoding="utf-8")

    return ContextBundle(
        task_id=task_id,
        story=story,
        iteration=iteration,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        title=task_row.title,
        objective=task_row.objective,
        success_criteria=task_row.success_criteria,
        scope_in=task_row.scope_in,
        scope_out=task_row.scope_out,
        plan_context=plan_context,
    )


def write_context_file(bundle: ContextBundle, output_path: Path) -> Path:
    """Render a context bundle as a markdown file and write it to output_path.

    Creates the parent directory if it does not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "---",
        f"task_id: {bundle.task_id}",
        f"story: {bundle.story}",
        f"iteration: {bundle.iteration}",
        f"generated_at: {bundle.generated_at}",
        "purpose: independent-verification",
        "---",
        "",
        f"# Verification Context: Task {bundle.task_id} — {bundle.title}",
        "",
        "## Task Requirements",
        "",
        bundle.objective or "_No objective recorded._",
        "",
        "## Success Criteria",
        "",
        bundle.success_criteria or "_No success criteria recorded._",
        "",
        "## Story Scope",
        "",
        "### In Scope",
        "",
        bundle.scope_in or "_Not specified._",
        "",
        "### Out of Scope",
        "",
        bundle.scope_out or "_Not specified._",
        "",
    ]

    if bundle.plan_context:
        lines += [
            "## Architecture Context",
            "",
            bundle.plan_context.strip(),
            "",
        ]

    lines += [
        "## Verification Guidelines",
        "",
        _VERIFICATION_GUIDELINES,
        "",
        "## Standards Reference",
        "",
        "Follow the code standards and patterns established in the story's architecture decisions.",
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class ContextResult:
    """Outcome of a context-generation operation."""

    output_path: Path
    task_id: int
    story: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "story": self.story,
            "output_path": str(self.output_path),
        }

    def __str__(self) -> str:
        return f"Context file: {self.output_path}"


@dataclass
class VerifyResult:
    """Outcome of a verify-submit operation."""

    task_id: int
    outcome: str
    result_file: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "outcome": self.outcome,
            "result_file": str(self.result_file),
        }

    def __str__(self) -> str:
        return f"Recorded verify_status={self.outcome} for task {self.task_id}"


# ── Commands ───────────────────────────────────────────────────────────────────


@command(name="context", help="Generate verifier context bundle.", group="verify")
def context(story: str, task_id: int) -> ContextResult:
    """Generate a verifier context bundle for the given task.

    Writes story{n}/verify/task-{id}-context.md with task requirements,
    success criteria, story scope, verification guidelines, and standards
    reference. Excludes work log content and implementation code.
    """
    stories_dir = get_stories_dir()
    db = StoryDB(stories_dir / story)
    bundle = build_context_bundle(db, stories_dir, story, task_id)
    output_path = (
        stories_dir / story / f"story{bundle.iteration}" / "verify" / f"task-{task_id}-context.md"
    )
    write_context_file(bundle, output_path)
    return ContextResult(output_path=output_path, task_id=task_id, story=story)


@command(name="verify-submit", help="Record verification result.", group="verify")
def verify_submit(
    story: str,
    task_id: int,
    outcome: Literal["pass", "fail"],
    message: Annotated[str | None, Arg(help="Findings.", short="-m")] = None,
) -> VerifyResult:
    """Record an independent verification result for the given task.

    Sets verify_status on the task record, writes a result artifact to
    story{n}/verify/task-{id}-result.md, and logs VERIFY_COMPLETE.
    The -m flag is required.
    """
    if message is None:
        raise WorkflowError("message is required for verify-submit")

    stories_dir = get_stories_dir()
    db = StoryDB(stories_dir / story)
    logger = StoryLogger(db.family_path / "story.db")

    state = db.get_state()
    if state is None:
        raise WorkflowError(f"Story '{story}' has no state. Has it been initialized?")

    iteration: int = state["current_plan"]
    task_row = db.get_task(task_id, plan_number=iteration)
    if task_row is None:
        raise WorkflowError(f"Task {task_id} not found in plan {iteration}.")

    db.update_task(task_id, plan_number=iteration, verify_status=outcome)

    verify_dir = stories_dir / story / f"story{iteration}" / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    result_file = verify_dir / f"task-{task_id}-result.md"

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    result_lines: list[str] = [
        "---",
        f"task_id: {task_id}",
        f"story: {story}",
        f"iteration: {iteration}",
        f"outcome: {outcome}",
        f"recorded_at: {now}",
        "---",
        "",
        f"# Verification Result: Task {task_id} — {task_row.title}",
        "",
        f"**Outcome:** {outcome}",
        "",
        "## Findings",
        "",
        message,
        "",
    ]
    result_file.write_text("\n".join(result_lines), encoding="utf-8")

    logger.log(
        "INFO",
        Events.VERIFY_COMPLETE,
        task_id=task_id,
        message=f"verify-submit {outcome}: {message}",
    )

    return VerifyResult(task_id=task_id, outcome=outcome, result_file=result_file)
