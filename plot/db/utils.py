"""Shared utility functions for the db package."""

from datetime import datetime


def _now() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.utcnow().isoformat() + "Z"
