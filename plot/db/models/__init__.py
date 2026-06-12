"""Domain models that cross the db abstraction boundary.

These types appear in protocol signatures (StoryStore, EventLogger) and must
therefore live above the concrete subpackages that implement those protocols.
Placing them here lets protocols.py and all concrete clients import from a
single, stable location with no cross-sibling dependencies.
"""

from .events import Events
from .log_row import LogRow
from .stage_row import StageRow
from .task_row import TaskRow

__all__ = ["Events", "LogRow", "StageRow", "TaskRow"]
