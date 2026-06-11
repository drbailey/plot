"""Protocols defining the stable contract for story storage and event logging.

Any class satisfying StoryStore or EventLogger can be used in place of the
SQLite implementations without changing call sites in core.
"""

from typing import Any, Protocol, runtime_checkable

from .logger.models import LogRow
from .story.models import StageRow, TaskRow


@runtime_checkable
class StoryStore(Protocol):
    """Read/write contract for story state, tasks, and stages."""

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
    ) -> None: ...

    def get_state(self) -> dict[str, Any] | None: ...

    def update_state(self, **kwargs: Any) -> None: ...

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
    ) -> None: ...

    def get_task(self, task_id: int, plan_number: int = 0) -> TaskRow | None: ...

    def get_tasks(self, plan_number: int = 0, status: str | None = None) -> list[TaskRow]: ...

    def update_task(self, task_id: int, plan_number: int = 0, **kwargs: Any) -> None: ...

    def add_stage(
        self,
        story: str,
        iteration: int,
        stage: str,
        status: str,
        skip_reason: str | None = None,
        artifact_paths: str | None = None,
    ) -> None: ...

    def get_stage(self, story: str, iteration: int, stage: str) -> StageRow | None: ...

    def update_stage(self, story: str, iteration: int, stage: str, **kwargs: Any) -> None: ...

    def get_stages(self, story: str, iteration: int | None = None) -> list[StageRow]: ...


@runtime_checkable
class EventLogger(Protocol):
    """Write/read contract for workflow event logs."""

    def log(
        self,
        level: str,
        event: str,
        task_id: int | None = None,
        message: str | None = None,
        exec_number: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None: ...

    def get_logs(
        self,
        limit: int = 100,
        event: str | None = None,
        task_id: int | None = None,
    ) -> list[LogRow]: ...
