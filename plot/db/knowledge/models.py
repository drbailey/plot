"""Data models for the cross-run knowledge store."""

from dataclasses import dataclass


@dataclass
class RunRow:
    """Represents a knowledge run entry."""

    id: int
    story: str
    iteration: int
    started_at: str
    completed_at: str | None = None
    outcome: str | None = None
    repo_paths: str | None = None


@dataclass
class PatternRow:
    """Represents a recorded pattern entry."""

    id: int
    run_id: int
    tag: str
    title: str
    description: str
    recorded_at: str
    frequency: int = 1
    context: str | None = None


@dataclass
class DecisionRow:
    """Represents a recorded decision entry."""

    id: int
    run_id: int
    story: str
    context: str
    decision: str
    rationale: str
    recorded_at: str


@dataclass
class ArtifactRow:
    """Represents a recorded artifact entry."""

    id: int
    run_id: int
    story: str
    iteration: int
    artifact_type: str
    file_path: str
    description: str
    recorded_at: str


@dataclass
class SearchResult:
    """A unified result from a cross-table knowledge search."""

    source: str  # "patterns", "decisions", or "artifacts"
    id: int
    recorded_at: str
    title: str | None = None
    description: str | None = None
    context: str | None = None
    frequency: int | None = None
