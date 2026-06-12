"""
plot.db — story workflow storage sublibrary.

Public API. Nothing outside this package should import from submodules directly;
import only from ``plot.db``. This keeps the SQLite implementation details behind
a stable interface that can be replaced without touching call sites.

Quick start::

    from plot.db import StoryDB, StoryLogger, KnowledgeDB, Events

    db = StoryDB("/path/to/stories/my-story")
    logger = StoryLogger(db.family_path / "story.db")
    knowledge = KnowledgeDB("/path/to/stories/knowledge.db")
"""

from .knowledge.client import KnowledgeDB
from .knowledge.models import ArtifactRow, DecisionRow, PatternRow, RunRow, SearchResult
from .logger.client import StoryLogger
from .models import Events, LogRow, StageRow, TaskRow
from .protocols import EventLogger, StoryStore
from .story.client import StoryDB

__all__ = [
    # Implementations
    "StoryDB",
    "StoryLogger",
    "KnowledgeDB",
    # Models
    "Events",
    "TaskRow",
    "LogRow",
    "StageRow",
    "RunRow",
    "PatternRow",
    "DecisionRow",
    "ArtifactRow",
    "SearchResult",
    # Protocols (stable contracts)
    "StoryStore",
    "EventLogger",
    # Convenience
    "get_db",
    "get_logger",
]


def get_db(story_path: str) -> StoryDB:
    """Return a StoryDB instance for the given story directory path."""
    return StoryDB(story_path)


def get_logger(db_path: str) -> StoryLogger:
    """Return a StoryLogger targeting the given story.db file path."""
    return StoryLogger(db_path)
