#!/usr/bin/env python3
"""
ReasonOS Replay and Diff Demo Script

Demonstrates:
1. Deterministic replay of a run
2. Diffing between original and replay (should be equivalent)
3. Diffing between two different runs (cross-run diff)
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append("src")

from reasonos.kernel import run_paper_verification_task
from reasonos.replay.replay_engine import replay_run
from reasonos.diff.run_diff import diff_runs
from reasonos.utils.validate import validate_rsl
from reasonos.utils.time import now_iso

def save_run(rsl, name, runs_dir):
    timestamp = now_iso().replace(":", "").replace("-", "").split(".")[0]
    output_file = runs_dir / f"run_{timestamp}_{name}.json"
    with open(output_file, "w") as f:
        json.dump(rsl, f, indent=2)
    return output_file

def main():
    print("=== ReasonOS Replay and Diff Demo ===")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    runs_dir = base_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    schema_path = str(base_dir / "specs/rsl/rsl.schema.json")
    
    document_path = str(data_dir / "demo_paper.txt")
    
    # === Part 1: Original Run ===
    paragraph_1 = "Model X improves accuracy by 15 percent on Dataset Y."
    print(f"\nRunning original task: '{paragraph_1}'")
    
    rsl_1 = run_paper_verification_task(
        paragraph=paragraph_1,
        document_path=document_path,
        policy_path="policies/default_policy.json"
    )
    
    run_path_1 = save_run(rsl_1, "original", runs_dir)
    print(f"Original run: {run_path_1}")
    
    # Validate schema
    try:
        validate_rsl(rsl_1, schema_path)
        print("Schema validation passed")
    except Exception as e:
        print(f"Schema validation FAILED: {e}")
        return

    # === Part 2: Replay ===
    print(f"\nReplaying run: {run_path_1}")
    original_run, replayed_run = replay_run(str(run_path_1))
    
    # Determine replay path (it was saved by replay_engine)
    # We can find it by looking for the latest file or just checking the return
    # The replay_engine saves it alongside the original.
    # Let's find it.
    replay_files = list(runs_dir.glob("*_replay_*.json"))
    replay_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    replay_path = replay_files[0]
    print(f"Replay run: {replay_path}")
    
    # Diff original vs replay
    diff_result = diff_runs(original_run, replayed_run)
    print(f"Replay diff summary: {diff_result['summary']}")
    
    if diff_result['step_diffs'] or diff_result['conclusion_diff']:
        print("WARNING: Unexpected differences found in replay!")
        print(json.dumps(diff_result, indent=2))
    
    # === Part 3: Cross Run Diff ===
    paragraph_2 = "Model X improves accuracy by 20 percent on Dataset Y."
    print(f"\n--- Cross Run Diff ---")
    print(f"Running modified task: '{paragraph_2}'")
    
    rsl_2 = run_paper_verification_task(
        paragraph=paragraph_2,
        document_path=document_path,
        policy_path="policies/default_policy.json"
    )
    save_run(rsl_2, "modified", runs_dir)
    
    # Diff run 1 vs run 2
    cross_diff = diff_runs(rsl_1, rsl_2)
    print(f"Diff summary: {cross_diff['summary']}")
    print(f"Step diffs: {len(cross_diff['step_diffs'])}")
    
    if cross_diff['conclusion_diff']:
        print("Conclusion diff detected.")
        
    # Verify audit hash exists
    if "run_hash" in rsl_1["audit"]:
        print("\nAudit hash verified present.")
    else:
        print("\nWARNING: Audit hash missing!")

if __name__ == "__main__":
    main()
