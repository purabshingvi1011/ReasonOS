#!/usr/bin/env python3
"""
ReasonOS Accounting Demo Script

Demonstrates:
1. Scenario A: Clean verification (Moderate cost, low risk)
2. Scenario B: Revision triggered (Higher cost, higher risk, confidence penalties)
3. Scenario C: Policy blocked (High risk, zero confidence)
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append("src")

from reasonos.kernel import run_paper_verification_task
from reasonos.utils.validate import validate_rsl
from reasonos.utils.time import now_iso

def save_run(rsl, name, runs_dir):
    timestamp = now_iso().replace(":", "").replace("-", "").split(".")[0]
    output_file = runs_dir / f"run_{timestamp}_{name}.json"
    with open(output_file, "w") as f:
        json.dump(rsl, f, indent=2)
    return output_file

def print_accounting(scenario_name, rsl):
    print(f"\n{scenario_name}")
    acc = rsl.get("accounting", {})
    if not acc:
        print("ERROR: No accounting object found!")
        return

    print(f"Total cost: {acc.get('total_cost')}")
    print(f"Total risk: {acc.get('total_risk')}")
    
    adjustments = acc.get("confidence_adjustments", [])
    if adjustments:
        print("Confidence adjustments:")
        for adj in adjustments:
            print(f"- {adj['source']}: {adj['delta']}")
            
    print(f"Final confidence: {acc.get('final_confidence')}")
    
    # Verify final confidence matches
    if rsl["final_conclusion"]["confidence"] != acc.get("final_confidence"):
        print(f"WARNING: Mismatch! Conclusion confidence {rsl['final_conclusion']['confidence']} != Accounting {acc.get('final_confidence')}")

def main():
    print("=== ReasonOS Accounting Demo ===")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    runs_dir = base_dir / "runs"
    runs_dir.mkdir(exist_ok=True)
    schema_path = str(base_dir / "specs/rsl/rsl.schema.json")
    
    document_path = str(data_dir / "demo_paper.txt")
    
    # === Scenario A: Clean verification ===
    # Claim: "Model X improves accuracy by 15 percent on Dataset Y."
    # Expect moderate cost, low risk, confidence ~0.65 (due to partial support / scope)
    rsl_a = run_paper_verification_task(
        paragraph="Model X improves accuracy by 15 percent on Dataset Y.",
        document_path=document_path,
        policy_path="policies/default_policy.json"
    )
    save_run(rsl_a, "accounting_scenario_a", runs_dir)
    print_accounting("Scenario A", rsl_a)
    validate_rsl(rsl_a, schema_path)

    # === Scenario B: Revision triggered ===
    # Claim: "Model X improves accuracy by 20 percent on Dataset Y."
    # Expect higher cost, higher risk, confidence ~0.85 after revision penalties
    rsl_b = run_paper_verification_task(
        paragraph="Model X improves accuracy by 20 percent on Dataset Y.",
        document_path=document_path,
        policy_path="policies/default_policy.json"
    )
    save_run(rsl_b, "accounting_scenario_b", runs_dir)
    print_accounting("Scenario B", rsl_b)
    validate_rsl(rsl_b, schema_path)

    # === Scenario C: Policy blocked ===
    # Claim: "Model X improves accuracy by 60 percent on Dataset Y."
    # Expect high risk (1.0), confidence 0.0
    rsl_c = run_paper_verification_task(
        paragraph="Model X improves accuracy by 60 percent on Dataset Y.",
        document_path=document_path,
        policy_path="policies/demo_policy.json"
    )
    save_run(rsl_c, "accounting_scenario_c", runs_dir)
    print_accounting("Scenario C", rsl_c)
    validate_rsl(rsl_c, schema_path)

if __name__ == "__main__":
    main()
