"""RSL document validation utilities."""

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError


def validate_rsl(doc: dict[str, Any], schema_path: str) -> None:
    """
    Validate an RSL document against the JSON Schema.

    Args:
        doc: The RSL document dictionary to validate.
        schema_path: Path to the JSON Schema file.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValidationError: If the document does not conform to the schema.
        ValueError: If the schema file cannot be parsed.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}") from e

    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))

    if errors:
        error_messages = []
        for error in errors:
            path_str = ".".join(str(p) for p in error.absolute_path) or "(root)"
            error_messages.append(f"  - {path_str}: {error.message}")
        raise ValidationError(
            f"RSL document validation failed:\n" + "\n".join(error_messages)
        )
