from dataclasses import dataclass


@dataclass
class StageRow:
    """Represents a stage entry."""

    story: str
    iteration: int
    stage: str
    status: str
    recorded_at: str
    skip_reason: str | None = None
    artifact_paths: str | None = None
