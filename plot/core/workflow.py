"""
Core story workflow logic.

This module is the library-level implementation of story lifecycle operations.
It has no knowledge of CLI mechanics, argparse, or output formatting.

Public API — class style (preferred for multi-step use)::

    wf = StoryWorkflow("my-story")
    result = wf.begin(repo_path="api_framework")

Public API — function style (convenience, one-shot)::

    from plot.core.workflow import begin, BeginResult

    result = begin(story="my-story", repo_path="api_framework")

Both raise WorkflowError (from plot.core.errors) on failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plot.cli.commands import command
from plot.core.config import get_stories_dir, resolve_repo_paths
from plot.core.errors import WorkflowError
from plot.core.scanner import ScanResult, scan_repos
from plot.db import Events, StoryDB, StoryLogger

APPROVAL_KEYWORD = "approve"

__all__ = ["StoryWorkflow", "BeginResult", "begin", "WorkflowError"]


# ── Result types ───────────────────────────────────────────────────────────────


@dataclass
class BeginResult:
    """Outcome of a begin operation."""

    mode: str  # "new" | "approve" | "revise" | "new_iteration"
    story: str
    iteration: int
    story_dir: Path
    repos: list[str] = field(default_factory=list)
    scan: ScanResult | None = None
    plan_file: Path | None = None
    user_context: str | None = None

    def to_dict(self) -> dict:  # type: ignore[type-arg]
        d: dict = {  # type: ignore[type-arg]
            "mode": self.mode,
            "story": self.story,
            "iteration": self.iteration,
            "story_dir": str(self.story_dir),
        }
        if self.repos:
            d["repos"] = self.repos
        if self.scan:
            d["scan"] = {
                "testing_available": self.scan.testing_available,
                "test_framework": self.scan.test_framework,
                "readme_exists": self.scan.readme_exists,
                "changelog_exists": self.scan.changelog_exists,
                "agent_config": self.scan.agent_config,
            }
        if self.plan_file is not None:
            d["plan_file"] = str(self.plan_file)
        if self.user_context is not None:
            d["user_context"] = self.user_context
        return d

    def __str__(self) -> str:
        lines = [
            f"MODE: {self.mode}",
            f"Story: {self.story} | Iteration: {self.iteration}",
            f"Story dir: {self.story_dir}",
        ]
        if self.mode == "new" and self.scan:
            lines.append(f"Repos: {', '.join(self.repos)}")
            testing = self.scan.test_framework or str(self.scan.testing_available)
            lines.append(
                f"Scan: testing={testing}, readme={self.scan.readme_exists},"
                f" changelog={self.scan.changelog_exists}"
            )
            if self.scan.agent_config:
                kinds = ", ".join(c["kind"] for c in self.scan.agent_config)
                lines.append(f"Agent config: {kinds}")
        elif self.mode == "approve":
            lines.append("Plan approved. Read plot/templates/task-creation.md to create tasks.")
        elif self.mode == "revise":
            if self.plan_file:
                lines.append(f"Plan file: {self.plan_file}")
            if self.user_context:
                lines.append(f"Feedback: {self.user_context}")
        elif self.mode == "new_iteration":
            lines.append(f"Repos: {', '.join(self.repos)}")
        return "\n".join(lines)


# ── Orchestration class ────────────────────────────────────────────────────────


class StoryWorkflow:
    """Orchestrates story lifecycle operations for a single named story.

    Holds ``db`` and ``logger`` as shared instance state so individual
    operations don't recreate them on every call.

    Args:
        story: Story name — used as the directory name under ``stories_dir``.
        stories_dir: Override the configured stories directory (useful for testing).
    """

    def __init__(self, story: str, stories_dir: Path | None = None) -> None:
        self.story = story
        self.stories_dir = stories_dir or get_stories_dir()
        self.story_path = self.stories_dir / story
        self.db = StoryDB(self.story_path)
        self.logger = StoryLogger(self.db.family_path / "story.db")

    # ── Public methods ─────────────────────────────────────────────────────────

    def begin(
        self,
        repo_path: str | None = None,
        max_iterations: int = 20,
        max_attempts: int = 3,
        user_context: str | None = None,
    ) -> BeginResult:
        """Detect begin mode and execute the appropriate workflow step.

        Args:
            repo_path: Comma-separated repo names or paths. Required for new stories.
            max_iterations: Maximum execution iterations for new stories.
            max_attempts: Maximum attempts per task for new stories.
            user_context: Free-text context; ``"approve"`` transitions planning → init.

        Returns:
            BeginResult describing what was done.

        Raises:
            WorkflowError: When the operation cannot proceed.
        """
        has_db = (self.story_path / "story.db").exists()
        resolved_repos = resolve_repo_paths(repo_path) if repo_path else []

        if not has_db and not resolved_repos:
            raise WorkflowError("New story requires a repo argument.")

        if not has_db:
            return self._begin_new(resolved_repos, max_iterations, max_attempts, user_context)

        state = self.db.get_state()
        if state is None:
            raise WorkflowError("story.db exists but has no state.")

        phase = state["phase"]

        if phase == "planning":
            user_ctx = (user_context or "").strip().lower()
            if user_ctx == APPROVAL_KEYWORD:
                return self._begin_approve(state)
            return self._begin_revise(state, user_context)

        if resolved_repos:
            return self._begin_new_iteration(state, resolved_repos, user_context)

        raise WorkflowError(f"Story is in '{phase}' phase. Use .continue for execution.")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _begin_new(
        self,
        resolved_repos: list[str],
        max_iterations: int,
        max_attempts: int,
        user_context: str | None,
    ) -> BeginResult:
        scan = scan_repos(resolved_repos)
        if not scan.repo_exists:
            errors = "; ".join(scan.errors)
            raise WorkflowError(f"Repository not found: {errors}")

        repo_path_str = ", ".join(resolved_repos)

        self.db.init_state(
            story=self.story,
            repo_path=repo_path_str,
            stories_dir=str(self.stories_dir),
            max_iterations=max_iterations,
            max_attempts_per_task=max_attempts,
            user_context=user_context,
            testing_available=scan.testing_available,
            readme_exists=scan.readme_exists,
            changelog_exists=scan.changelog_exists,
        )
        self.db.update_state(phase="planning")

        iteration = 0
        story_dir = self.story_path / f"story{iteration}"
        (story_dir / "plan").mkdir(parents=True, exist_ok=True)

        self.logger.log(
            "INFO",
            Events.WORKFLOW_INIT,
            task_id=0,
            message=f"Initialized story '{self.story}'",
            details={
                "repos": resolved_repos,
                "testing_available": scan.testing_available,
                "test_framework": scan.test_framework,
                "readme_exists": scan.readme_exists,
                "changelog_exists": scan.changelog_exists,
                "agent_config_count": len(scan.agent_config),
            },
        )

        return BeginResult(
            mode="new",
            story=self.story,
            iteration=iteration,
            story_dir=story_dir,
            repos=resolved_repos,
            scan=scan,
        )

    def _begin_approve(self, state: dict) -> BeginResult:  # type: ignore[type-arg]
        iteration = state["current_plan"]
        story_dir = self.story_path / f"story{iteration}"
        plan_file = story_dir / "plan" / "plan.md"

        if not plan_file.exists():
            raise WorkflowError(f"No plan.md found at {plan_file}.")

        self.db.update_state(phase="init", last_signal="PLAN_APPROVED")
        self.logger.log(
            "INFO",
            Events.PLAN_APPROVED,
            task_id=0,
            message="Plan approved, ready for task creation",
        )

        return BeginResult(
            mode="approve",
            story=self.story,
            iteration=iteration,
            story_dir=story_dir,
            plan_file=plan_file,
        )

    def _begin_revise(self, state: dict, user_context: str | None) -> BeginResult:  # type: ignore[type-arg]
        iteration = state["current_plan"]
        story_dir = self.story_path / f"story{iteration}"
        plan_file = story_dir / "plan" / "plan.md"

        self.logger.log("INFO", Events.PLAN_REVISION, task_id=0, message="Plan revision requested")

        return BeginResult(
            mode="revise",
            story=self.story,
            iteration=iteration,
            story_dir=story_dir,
            plan_file=plan_file if plan_file.exists() else None,
            user_context=user_context,
        )

    def _begin_new_iteration(
        self,
        state: dict,  # type: ignore[type-arg]
        resolved_repos: list[str],
        user_context: str | None,
    ) -> BeginResult:
        new_iteration = state["current_plan"] + 1
        story_dir = self.story_path / f"story{new_iteration}"
        (story_dir / "plan").mkdir(parents=True, exist_ok=True)

        repo_path_str = ", ".join(resolved_repos)
        scan = scan_repos(resolved_repos)

        self.db.update_state(
            current_plan=new_iteration,
            phase="planning",
            current_task=None,
            last_signal="NEW_PLAN_CREATED",
            last_exec_number=0,
            testing_available=scan.testing_available,
            readme_exists=scan.readme_exists,
            changelog_exists=scan.changelog_exists,
        )
        if repo_path_str != state.get("repo_path"):
            self.db.update_state(repo_path=repo_path_str)
        if user_context:
            self.db.update_state(user_context=user_context)

        self.logger.log(
            "INFO",
            Events.NEW_PLAN,
            task_id=0,
            message=f"Created story{new_iteration}",
        )

        return BeginResult(
            mode="new_iteration",
            story=self.story,
            iteration=new_iteration,
            story_dir=story_dir,
            repos=resolved_repos,
            scan=scan,
            user_context=user_context,
        )


# ── Convenience wrapper ────────────────────────────────────────────────────────


@command(name="begin", help="Begin, revise, or approve a story.", group="story")
def begin(
    story: str,
    repo_path: str | None = None,
    max_iterations: int = 20,
    max_attempts: int = 3,
    user_context: str | None = None,
) -> BeginResult:
    """One-shot convenience wrapper around ``StoryWorkflow.begin()``.

    The ``stories_dir`` override is available via ``StoryWorkflow`` directly.
    """
    return StoryWorkflow(story).begin(
        repo_path=repo_path,
        max_iterations=max_iterations,
        max_attempts=max_attempts,
        user_context=user_context,
    )
