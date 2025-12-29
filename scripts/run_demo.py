#!/usr/bin/env python3
"""ReasonOS demo runner.

This script demonstrates the ReasonOS microkernel by running a demo task
that calculates a loan payment, validates the RSL output, and writes
the result to a file.

Usage:
    python scripts/run_demo.py

This script must be run from the repository root directory.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from reasonos.kernel import run_demo_task
from reasonos.utils.validate import validate_rsl


def main() -> int:
    """
    Run the demo task, validate output, and write to file.

    Returns:
        0 on success, 1 on error.
    """
    # Define paths
    schema_path = REPO_ROOT / "specs" / "rsl" / "rsl.schema.json"
    runs_dir = REPO_ROOT / "runs"

    # Ensure runs directory exists
    runs_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Execute the demo task
        rsl_doc = run_demo_task()

        # Validate against schema
        validate_rsl(rsl_doc, str(schema_path))

        # Generate output filename with UTC timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        output_file = runs_dir / f"run_{timestamp}.json"

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(rsl_doc, f, indent=2)

        # Print required outputs
        print(output_file.relative_to(REPO_ROOT))
        print("Schema validation passed")
        print(rsl_doc["final_conclusion"]["content"])

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
