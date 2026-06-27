"""Common utility functions."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Get current UTC time. Use as default for datetime columns."""
    return datetime.now(timezone.utc)
