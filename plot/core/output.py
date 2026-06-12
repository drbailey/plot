"""
Library output utilities.

emit(message, level) prints to stdout when level <= default_verbosity.
Level 0 always prints; higher levels are increasingly verbose.

emit_result(result, output_json) formats and emits any result object that
implements to_dict() and __str__(). Called by the CLI dispatcher after a
successful command; core functions never call it directly.

Callers set verbosity directly:  output.default_verbosity = 1
"""

import json
import sys
from typing import Any

default_verbosity: int = 0


def emit(message: str, level: int = 0) -> None:
    """Print message if level <= default_verbosity."""
    if level <= default_verbosity:
        print(message, file=sys.stdout)


def emit_result(result: Any, *, output_json: bool = False) -> None:
    """Emit a result object as human-readable text or JSON.

    The result must implement ``to_dict()`` (for JSON) and ``__str__()``
    (for text). All result dataclasses in plot.core should provide both.
    """
    if output_json:
        emit(json.dumps(result.to_dict(), indent=2))
    else:
        emit(str(result))
