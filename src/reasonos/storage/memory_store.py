"""Disk-backed memory store for ReasonOS.

Provides persistent storage for memory writes across runs.
"""

import json
from pathlib import Path
from typing import Any, Callable


class MemoryStoreError(Exception):
    """Raised when memory store operations fail."""

    pass


def load_memory(memory_path: str) -> list[dict[str, Any]]:
    """
    Load memory from a JSON file.

    Args:
        memory_path: Path to the memory JSON file.

    Returns:
        List of memory write dictionaries. Returns empty list if file
        does not exist or is empty.

    Raises:
        MemoryStoreError: If JSON parsing fails.
    """
    path = Path(memory_path)

    if not path.exists():
        return []

    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []

        data = json.loads(content)

        if not isinstance(data, list):
            raise MemoryStoreError(
                f"Memory file must contain a JSON array: {memory_path}"
            )

        return data

    except json.JSONDecodeError as e:
        raise MemoryStoreError(
            f"Invalid JSON in memory file {memory_path}: {e}"
        ) from e


def append_memory(memory_path: str, writes: list[dict[str, Any]]) -> None:
    """
    Append memory writes to the memory file.

    Creates parent directories and the file if they do not exist.

    Args:
        memory_path: Path to the memory JSON file.
        writes: List of memory write dictionaries to append.

    Raises:
        MemoryStoreError: If file operations fail.
    """
    if not writes:
        return

    path = Path(memory_path)

    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing memory
    existing = load_memory(memory_path)

    # Append new writes
    updated = existing + writes

    # Write back with stable formatting
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)
    except OSError as e:
        raise MemoryStoreError(
            f"Failed to write memory file {memory_path}: {e}"
        ) from e


def query_memory(
    memory_items: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """
    Filter memory items using a predicate function.

    Args:
        memory_items: List of memory write dictionaries.
        predicate: Function that returns True for items to include.

    Returns:
        List of memory items that match the predicate.
    """
    return [item for item in memory_items if predicate(item)]


def clear_memory(memory_path: str) -> None:
    """
    Clear all memory from the file.

    Args:
        memory_path: Path to the memory JSON file.
    """
    path = Path(memory_path)
    if path.exists():
        path.write_text("[]", encoding="utf-8")
