"""
Library-wide exception types for plot.core.

Import from here rather than from individual modules:

    from plot.core.errors import WorkflowError, PlotError
"""


class PlotError(Exception):
    """Base class for all plot library errors."""


class WorkflowError(PlotError):
    """Raised when a story workflow operation cannot proceed."""
