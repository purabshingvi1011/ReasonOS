#!/usr/bin/env python3
"""
ReasonOS SDK Demo Script

Demonstrates the public Developer API:
1. Initialize ReasonOSClient
2. Verify a research claim
3. Access structured results (conclusion, confidence, accounting)
4. Replay the run deterministically
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append("src")

from reasonos.sdk.client import ReasonOSClient
from reasonos.utils.validate import validate_rsl

def main():
    print("=== ReasonOS SDK Demo ===")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    runs_dir = base_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    schema_path = str(base_dir / "specs/rsl/rsl.schema.json")
    
    document_path = str(data_dir / "demo_paper.txt")
    
    # 1. Initialize Client
    client = ReasonOSClient(
        policy_path="policies/default_policy.json",
        enable_replay=True
    )
    
    # 2. Verify Research Claim
    claim = "Model X improves accuracy by 15 percent on Dataset Y."
    print(f"Verifying claim: '{claim}'")
    
    try:
        rsl = client.verify_research_claim(
            claim=claim,
            document_path=document_path
        )
        
        # Validate schema (internal check)
        validate_rsl(rsl, schema_path)
        
        # 3. Print Summary
        conclusion = rsl.get("final_conclusion", {})
        accounting = rsl.get("accounting", {})
        
        content = conclusion.get('content', '')
        if "Confidence:" in content:
            content = content.split("Confidence:")[0].strip()
        print(f"Final conclusion: {content}")
        print(f"Confidence: {conclusion.get('confidence')}")
        print("Accounting:")
        print(f"  Total cost: {accounting.get('total_cost')}")
        print(f"  Total risk: {accounting.get('total_risk')}")
        
        # Save run for replay test
        run_id = rsl["run"]["run_id"]
        output_file = runs_dir / f"sdk_demo_run_{run_id}.json"
        with open(output_file, "w") as f:
            json.dump(rsl, f, indent=2)
            
        # 4. Replay Run
        print("\nReplaying run...")
        replayed_rsl = client.replay_run(str(output_file))
        
        # Verify equivalence
        orig_hash = rsl.get("audit", {}).get("run_hash")
        replay_hash = replayed_rsl.get("audit", {}).get("run_hash")
        
        if orig_hash == replay_hash:
            print("Replay successful. Runs equivalent.")
        else:
            print(f"Replay FAILED. Hash mismatch: {orig_hash} != {replay_hash}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
