from dataclasses import dataclass
from typing import Any


@dataclass
class LogRow:
    """Represents a log entry."""

    id: int
    timestamp: str
    level: str
    event: str
    exec_number: int | None = None
    task_id: int | None = None
    message: str | None = None
    details: dict[str, Any] | None = None
