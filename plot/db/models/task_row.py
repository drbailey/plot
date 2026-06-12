from dataclasses import dataclass


@dataclass
class TaskRow:
    """Represents a task row from the database."""

    task_id: int
    plan_number: int
    title: str
    status: str
    attempts: int
    dependencies: list[int]
    created_at: str
    updated_at: str
    objective: str | None = None
    success_criteria: str | None = None
    scope_in: str | None = None
    scope_out: str | None = None
    approach: str | None = None
    notes: str | None = None
    work_log: str | None = None
    verify_status: str | None = None
    verify_file: str | None = None
