#!/usr/bin/env python3
"""
ReasonOS Multi-Model Demo Script

Demonstrates routing steps to different executors (GPT, O3, Retriever)
based on policy rules.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append("src")

from reasonos.kernel import run_paper_verification_task
from reasonos.utils.validate import validate_rsl
from reasonos.utils.ids import new_run_id
from reasonos.utils.time import now_iso

def main():
    print("=== ReasonOS Multi-Model Demo ===")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    runs_dir = base_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    schema_path = str(base_dir / "specs/rsl/rsl.schema.json")
    
    document_path = str(data_dir / "demo_paper.txt")
    
    # Scenario: Claim supported by document
    paragraph = "Model X improves accuracy by 15 percent on Dataset Y."
    
    print(f"Scenario: Verifying claim '{paragraph}'")
    print("Expected behavior: Steps routed to different executors (GPT, Retriever, O3).")
    
    try:
        # Run the task
        # Note: default_policy.json now contains the routing rules
        rsl = run_paper_verification_task(
            paragraph=paragraph,
            document_path=document_path,
            policy_path="policies/default_policy.json"
        )
        
        # Validate RSL
        try:
            validate_rsl(rsl, schema_path)
            print("Schema validation: PASSED")
            is_valid = True
        except Exception as e:
            print(f"Schema validation: FAILED - {e}")
            is_valid = False
        
        # Save run output
        run_id = rsl["run"]["run_id"]
        timestamp = now_iso().replace(":", "").replace("-", "").split(".")[0]
        output_file = runs_dir / f"run_{timestamp}_multimodel_demo.json"
        
        with open(output_file, "w") as f:
            json.dump(rsl, f, indent=2)
            
        print(f"\nRun completed. Output saved to: {output_file}")
        
        # Check executors
        steps = rsl["steps"]
        print("\nExecutor Usage:")
        for step in steps:
            step_id = step.get("step_id")
            step_index = step.get("step_index")
            executor = step.get("executor", {})
            executor_name = executor.get("name", "unknown")
            
            # Also check execution metadata
            execution = step.get("execution", {})
            executor_used = execution.get("executor_used", "unknown")
            
            print(f"S{step_index + 1} executor: {executor_name} (Used: {executor_used})")
            
        # Check final conclusion
        conclusion = rsl["final_conclusion"]
        print(f"\nFinal Conclusion: {conclusion['content']}")
            
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
