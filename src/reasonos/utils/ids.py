"""ID generation utilities for ReasonOS entities."""

from uuid import uuid4


def new_task_id() -> str:
    """Generate a new unique task ID."""
    return f"task_{uuid4().hex[:12]}"


def new_run_id() -> str:
    """Generate a new unique run ID."""
    return f"run_{uuid4().hex[:12]}"


def new_step_id() -> str:
    """Generate a new unique step ID."""
    return f"step_{uuid4().hex[:12]}"


def new_evidence_id() -> str:
    """Generate a new unique evidence ID."""
    return f"ev_{uuid4().hex[:12]}"


def new_event_id() -> str:
    """Generate a new unique event ID."""
    return f"evt_{uuid4().hex[:12]}"


def new_memory_id() -> str:
    """Generate a new unique memory ID."""
    return f"mem_{uuid4().hex[:12]}"


def new_contradiction_id() -> str:
    """Generate a new unique contradiction ID."""
    return f"ctr_{uuid4().hex[:12]}"


def new_revision_id() -> str:
    """Generate a new unique revision ID."""
    return f"rev_{uuid4().hex[:12]}"


