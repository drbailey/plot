"""Combined schema for the story database.

StoryDB manages both story state and event logs in a single SQLite file.
This module assembles the combined DDL so story/client.py does not need to
import from the logger subpackage.
"""

from .logger.schema import SCHEMA as _LOGGING_SCHEMA
from .story.schema import SCHEMA as _STORY_SCHEMA

STORY_DB_SCHEMA: str = _STORY_SCHEMA + _LOGGING_SCHEMA
