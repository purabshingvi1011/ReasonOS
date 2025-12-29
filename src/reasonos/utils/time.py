"""Time utilities for ReasonOS."""

from datetime import datetime, timezone


def now_iso() -> str:
    """Return current UTC time as ISO 8601 string ending in Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
