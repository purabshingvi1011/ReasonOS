"""Contradiction detection for ReasonOS.

Provides deterministic detection of numeric conflicts across memory.
"""

import re
from typing import Any

from ..utils.ids import new_contradiction_id
from ..utils.time import now_iso


def extract_percent(text: str) -> float | None:
    """
    Extract the first percentage value from text.

    Matches patterns like "15 percent", "14.8 percent", "15%".

    Args:
        text: The text to search for percentage values.

    Returns:
        The numeric value as a float, or None if no match found.
    """
    pattern = r"(\d+(?:\.\d+)?)\s*(?:percent|%)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def detect_numeric_contradictions(
    memory_items: list[dict[str, Any]],
    current_subject: str,
    current_value: float,
    unit: str,
    threshold: float,
) -> list[dict[str, Any]]:
    """
    Detect numeric contradictions between current value and memory.

    Searches memory for FACTs mentioning the same subject and compares
    numeric values.

    Args:
        memory_items: List of memory write dictionaries.
        current_subject: Subject string to match (case insensitive).
        current_value: Current numeric value to compare.
        unit: Unit of measurement (e.g., "percent").
        threshold: Maximum allowed difference before contradiction.

    Returns:
        List of contradiction records for any detected conflicts.
    """
    contradictions = []
    subject_lower = current_subject.lower()

    for item in memory_items:
        # Only check FACT type memories
        if item.get("type") != "FACT":
            continue

        content = item.get("content", "")
        content_lower = content.lower()

        # Check if subject is mentioned (case insensitive containment)
        # For "Model X Dataset Y", check both parts
        subject_parts = subject_lower.split()
        if not all(part in content_lower for part in subject_parts):
            continue

        # Extract percent value from memory content
        memory_value = extract_percent(content)
        if memory_value is None:
            continue

        # Check for contradiction
        diff = abs(memory_value - current_value)
        if diff > threshold:
            contradiction = {
                "contradiction_id": new_contradiction_id(),
                "step_ids": ["S3"],
                "description": (
                    f"Numeric conflict detected: current claim states {current_value}{unit}, "
                    f"but prior memory recorded {memory_value}{unit} for the same subject. "
                    f"Difference of {diff:.1f}{unit} exceeds threshold of {threshold}{unit}."
                ),
                "severity": "HIGH",
                "detected_by": {
                    "type": "RULE",
                    "name": "numeric_conflict_detector",
                },
                "detected_at": now_iso(),
                "prior_memory_id": item.get("memory_id"),
                "prior_value": memory_value,
                "current_value": current_value,
            }
            contradictions.append(contradiction)

    return contradictions
