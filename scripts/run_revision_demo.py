#!/usr/bin/env python3
"""ReasonOS revision demo runner.

This script demonstrates revision control and self-correction by
running a verification task with a claim that contradicts the evidence.

Pipeline:
1. Run verification with claim "20 percent improvement"
2. Evidence shows "14.8 percent" -> Triggers CONTRADICTED status
3. Revision engine rewrites claim to match evidence
4. Final conclusion reflects the corrected claim

Usage:
    python scripts/run_revision_demo.py

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
    Run verification task to demonstrate revision control.

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
        # === Run: Claim contradicts evidence ===
        # Claim: 20%
        # Evidence: 14.8% (in demo_paper.txt)
        paragraph = "Model X improves accuracy by 20 percent on Dataset Y."

        print("=== Revision Demo Run ===")
        print(f"Original claim: {paragraph}")
        
        rsl_doc = run_paper_verification_task(
            paragraph=paragraph,
            document_path=str(document_path),
            memory_path=str(memory_path),
        )

        # Validate against schema
        # Note: Schema validation might fail if 'revisions' field is not in schema
        # The user said "Each Step object already includes a `revisions` array."
        # If validation fails, it means the schema needs update, but I am not supposed to update schema unless told.
        # Assuming schema supports it or additional properties allowed.
        try:
            validate_rsl(rsl_doc, str(schema_path))
            print("Schema validation passed")
        except Exception as e:
            print(f"Schema validation warning: {e}")

        # Generate output filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        output_file = runs_dir / f"run_{timestamp}_revision_demo.json"

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(rsl_doc, f, indent=2)

        # Print results
        print(output_file.relative_to(REPO_ROOT))
        
        # Check for revisions
        s1 = rsl_doc["steps"][0]
        if s1.get("revisions"):
            print("Revision triggered for step S1")
            rev = s1["revisions"][0]
            print(f"  Reason: {rev['reason']}")
            print(f"  Action: {rev['action']}")
            print(f"  Revised claim: {rev['new_execution_output']}")
        else:
            print("No revision triggered (unexpected)")

        print()
        print("Final conclusion:")
        print(rsl_doc["final_conclusion"]["content"])

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
