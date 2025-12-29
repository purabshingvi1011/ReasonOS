from typing import Any, Dict, List, Optional

def diff_runs(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two runs and compute a structured diff.
    
    Args:
        run_a: First run dictionary.
        run_b: Second run dictionary.
        
    Returns:
        RunDiff dictionary with summary and detailed diffs.
    """
    step_diffs = []
    conclusion_diff = None
    
    # Compare steps
    steps_a = run_a.get("steps", [])
    steps_b = run_b.get("steps", [])
    
    # Map steps by step_index (assuming stable indexing)
    steps_a_map = {s.get("step_index"): s for s in steps_a}
    steps_b_map = {s.get("step_index"): s for s in steps_b}
    
    all_indices = sorted(set(steps_a_map.keys()) | set(steps_b_map.keys()))
    
    for idx in all_indices:
        s_a = steps_a_map.get(idx)
        s_b = steps_b_map.get(idx)
        
        if not s_a:
            step_diffs.append({
                "step_index": idx,
                "type": "ADDED",
                "details": "Step present in Run B but not Run A"
            })
            continue
            
        if not s_b:
            step_diffs.append({
                "step_index": idx,
                "type": "REMOVED",
                "details": "Step present in Run A but not Run B"
            })
            continue
            
        # Compare fields
        diffs = []
        
        # Execution output
        if s_a.get("execution_output") != s_b.get("execution_output"):
            diffs.append({
                "field": "execution_output",
                "before": s_a.get("execution_output"),
                "after": s_b.get("execution_output")
            })
            
        # Verification status
        v_a = s_a.get("verification", {})
        v_b = s_b.get("verification", {})
        
        if v_a.get("result") != v_b.get("result"):
            diffs.append({
                "field": "verification.result",
                "before": v_a.get("result"),
                "after": v_b.get("result")
            })
            
        if v_a.get("confidence") != v_b.get("confidence"):
             diffs.append({
                "field": "verification.confidence",
                "before": v_a.get("confidence"),
                "after": v_b.get("confidence")
            })
            
        # Revisions
        rev_a = s_a.get("revisions", [])
        rev_b = s_b.get("revisions", [])
        if len(rev_a) != len(rev_b):
             diffs.append({
                "field": "revisions_count",
                "before": len(rev_a),
                "after": len(rev_b)
            })
            
        if diffs:
            step_diffs.append({
                "step_index": idx,
                "step_id_a": s_a.get("step_id"), # Informational
                "type": "MODIFIED",
                "changes": diffs
            })
            
    # Compare final conclusion
    fc_a = run_a.get("final_conclusion", {})
    fc_b = run_b.get("final_conclusion", {})
    
    fc_diffs = []
    if fc_a.get("content") != fc_b.get("content"):
        fc_diffs.append({
            "field": "content",
            "before": fc_a.get("content"),
            "after": fc_b.get("content")
        })
        
    if fc_a.get("confidence") != fc_b.get("confidence"):
        fc_diffs.append({
            "field": "confidence",
            "before": fc_a.get("confidence"),
            "after": fc_b.get("confidence")
        })
        
    if fc_diffs:
        conclusion_diff = {
            "type": "MODIFIED",
            "changes": fc_diffs
        }
        
    # Summary
    if not step_diffs and not conclusion_diff:
        summary = "Runs are equivalent except for metadata."
    else:
        parts = []
        if conclusion_diff:
            parts.append("Final conclusion changed")
        if step_diffs:
            parts.append(f"Step execution/verification changed in {len(step_diffs)} step(s)")
        summary = " and ".join(parts) + "."
        
    return {
        "summary": summary,
        "step_diffs": step_diffs,
        "conclusion_diff": conclusion_diff
    }
