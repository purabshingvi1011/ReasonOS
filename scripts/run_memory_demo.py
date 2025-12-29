#!/usr/bin/env python3
"""ReasonOS memory demo runner.

This script demonstrates persistent memory and contradiction detection by
running two verification tasks back to back with different claims about
the same subject.

Run 1: Claims 15% improvement (partially supported, writes memory)
Run 2: Claims 20% improvement (contradicts prior memory)

Usage:
    python scripts/run_memory_demo.py

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

from reasonos.kernel import run_paper_verification_task
from reasonos.utils.validate import validate_rsl
from reasonos.storage.memory_store import clear_memory


def main() -> int:
    """
    Run two verification tasks to demonstrate memory and contradiction detection.

    Returns:
        0 on success, 1 on error.
    """
    # Define paths
    schema_path = REPO_ROOT / "specs" / "rsl" / "rsl.schema.json"
    runs_dir = REPO_ROOT / "runs"
    document_path = REPO_ROOT / "data" / "demo_paper.txt"
    memory_path = REPO_ROOT / "data" / "memory.json"

    # Ensure runs directory exists
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Clear memory for clean demo
    clear_memory(str(memory_path))

    try:
        # === Run 1: First claim ===
        paragraph_1 = "Model X improves accuracy by 15 percent on Dataset Y."

        print("=== Run 1 ===")
        rsl_doc_1 = run_paper_verification_task(
            paragraph=paragraph_1,
            document_path=str(document_path),
            memory_path=str(memory_path),
        )

        # Validate against schema
        validate_rsl(rsl_doc_1, str(schema_path))

        # Generate output filename
        timestamp_1 = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        output_file_1 = runs_dir / f"run_{timestamp_1}_memory_demo_1.json"

        # Write to file
        with open(output_file_1, "w", encoding="utf-8") as f:
            json.dump(rsl_doc_1, f, indent=2)

        # Print results
        print(output_file_1.relative_to(REPO_ROOT))
        print("Schema validation passed")
        print(f"Memory file updated: {memory_path.relative_to(REPO_ROOT)}")
        print()

        # === Run 2: Conflicting claim ===
        paragraph_2 = "Model X improves accuracy by 20 percent on Dataset Y."

        print("=== Run 2 ===")
        rsl_doc_2 = run_paper_verification_task(
            paragraph=paragraph_2,
            document_path=str(document_path),
            memory_path=str(memory_path),
        )

        # Validate against schema
        validate_rsl(rsl_doc_2, str(schema_path))

        # Generate output filename
        timestamp_2 = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        output_file_2 = runs_dir / f"run_{timestamp_2}_memory_demo_2.json"

        # Write to file
        with open(output_file_2, "w", encoding="utf-8") as f:
            json.dump(rsl_doc_2, f, indent=2)

        # Print results
        print(output_file_2.relative_to(REPO_ROOT))
        print("Schema validation passed")

        # Check for contradictions
        if rsl_doc_2.get("contradictions"):
            print("Contradiction detected!")
            for c in rsl_doc_2["contradictions"]:
                print(f"  Severity: {c['severity']}")
                print(f"  Description: {c['description']}")
        else:
            print("No contradictions detected")

        print()
        print("Final conclusion:")
        print(rsl_doc_2["final_conclusion"]["content"])

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
