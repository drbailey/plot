"""
Base class for CLI result objects.

All result dataclasses that have a simple one-to-one mapping between their
dataclass fields and the desired dict output should inherit from Result.
The generic to_dict() uses dataclasses.asdict(), which recursively converts
nested dataclasses to dicts (useful for results that carry TaskRow, LogRow,
etc. as fields).

Results that need a custom dict shape (e.g. selecting a subset of nested
fields, or wrapping a pre-built dict) should override to_dict() directly.
"""

from __future__ import annotations

import dataclasses
from typing import Any


@dataclasses.dataclass
class Result:
    """Mixin base for CLI result dataclasses.

    Provides a generic to_dict() via dataclasses.asdict(). Every subclass
    must also implement __str__() for human-readable output.
    """

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)
