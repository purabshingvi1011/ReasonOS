#!/usr/bin/env python3
"""
ReasonOS Policy Demo Script

Demonstrates the policy layer blocking an output due to insufficient confidence.
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
    print("=== ReasonOS Policy Demo ===")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    runs_dir = base_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    schema_path = str(base_dir / "specs/rsl/rsl.schema.json")
    
    document_path = str(data_dir / "demo_paper.txt")
    
    # Scenario: Claim that is not supported by the document
    # Document says 53.5% on Dataset A.
    # Claim says 60% on Dataset Y.
    # This should result in WEAK support (or CONTRADICTED) and low confidence.
    # With max_revisions_per_step=0 in demo_policy, revision is disallowed, triggering a block.
    paragraph = "Model X improves accuracy by 60 percent on Dataset Y."
    
    print(f"Scenario: Verifying claim '{paragraph}'")
    print("Expected behavior: Policy should BLOCK this output due to low confidence.")
    
    try:
        # Run the task
        rsl = run_paper_verification_task(
            paragraph=paragraph,
            document_path=document_path,
            policy_path="policies/demo_policy.json"
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
        output_file = runs_dir / f"run_{timestamp}_policy_demo.json"
        
        with open(output_file, "w") as f:
            json.dump(rsl, f, indent=2)
            
        print(f"\nRun completed. Output saved to: {output_file}")
            
        # Check results
        conclusion = rsl["final_conclusion"]
        confidence = conclusion["confidence"]
        content = conclusion["content"]
        
        print(f"\nFinal Conclusion Confidence: {confidence}")
        print(f"Final Conclusion Content: {content}")
        
        if confidence == 0.0 and "blocked" in content.lower():
            print("\nSUCCESS: Policy correctly blocked the output.")
        else:
            print("\nFAILURE: Policy did not block the output as expected.")
            
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
