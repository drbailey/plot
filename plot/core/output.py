"""
CLI output utilities with verbosity control.

Replaces broadcast.py from v1 with a cleaner emit/set_verbosity interface.
"""

import logging
import sys

# Level for output that should always be shown regardless of verbosity setting.
OUTPUT = 100

_verbosity: int = logging.INFO


def emit(message: str, level: int = OUTPUT) -> None:
    """
    Print a message if it meets the verbosity threshold.

    Messages at logging.ERROR or above are written to stderr; all others to stdout.
    """
    if level < _verbosity:
        return
    file = sys.stderr if level >= logging.ERROR else sys.stdout
    print(message, file=file)
