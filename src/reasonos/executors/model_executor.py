"""Model executor stub for ReasonOS.

This is a deterministic stub executor that simulates model inference
without making any actual LLM API calls.
"""

from typing import Any


def execute(step: dict[str, Any], context: dict[str, Any]) -> str:
    """
    Execute a model inference step (stub implementation).

    This stub executor returns a deterministic response suitable for
    the loan payment demo task.

    Args:
        step: The step dictionary containing action and metadata.
        context: Additional context for execution.

    Returns:
        A deterministic string representing the model's output.
    """
    # For the demo task S1, always return the formula selection response
    return "Use the standard amortized loan payment formula."
