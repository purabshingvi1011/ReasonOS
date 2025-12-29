from typing import List, Dict, Any, Optional

def apply_step_policy(policy: Dict[str, Any], domain: str, steps: List[Dict[str, Any]]) -> None:
    """
    Applies policy rules to a list of steps.
    
    Enforces evidence requirements and revision limits.
    Modifies the steps in-place.
    
    Args:
        policy: The loaded policy dictionary.
        domain: The domain of the task (e.g., "research_verification").
        steps: List of step dictionaries.
    """
    domain_defaults = policy.get("domain_defaults", {}).get(domain, {})
    evidence_required_steps = domain_defaults.get("evidence_required_steps", [])
    max_revisions = domain_defaults.get("max_revisions_per_step", 100) # Default high if not set

    for step in steps:
        # Enforce evidence required
        # Check by step_id (e.g. "S2") or step_index if needed, but requirements say "step_ids or step titles"
        # In ReasonOS, step_ids are UUIDs, but the policy uses logical names like "S2".
        # The kernel assigns IDs dynamically.
        # However, the prompt says: "If a step_id is in evidence_required_steps".
        # But wait, in the kernel `s2_id = new_step_id()`. The policy config has "S2".
        # The prompt example says: "evidence_required_steps includes: 'S2', 'S3'".
        # This implies I need a way to map logical step names to actual steps.
        # In the kernel, steps don't have a "logical name" field like "S2".
        # But they have `step_index`. "S2" usually means index 1 (S1 is index 0).
        # OR, maybe the user intends for me to match based on something else?
        # "step_ids or step titles". Step titles might be the `action`?
        # Let's look at the kernel again.
        # `s2 = build_step(step_id=s2_id, step_index=1, ...)`
        # If the policy says "S2", it likely refers to the step at index 1 (0-indexed? or 1-indexed?).
        # Usually S1 is index 0, S2 is index 1.
        # Let's assume "S{N}" maps to step_index N-1.
        # Also, the prompt says "step_ids or step titles".
        # If I can't match by ID (since they are random UUIDs), I should try to match by index if the string is "S<number>".
        
        # Let's implement a helper to check if a step matches the policy identifier.
        
        step_index = step.get("step_index")
        step_id = step.get("step_id")
        
        should_require_evidence = False
        
        for identifier in evidence_required_steps:
            # Check if identifier is "S<number>"
            if identifier.startswith("S") and identifier[1:].isdigit():
                target_index = int(identifier[1:]) - 1
                if step_index == target_index:
                    should_require_evidence = True
                    break
            # Check if identifier matches step_id (unlikely for dynamic IDs but possible)
            if identifier == step_id:
                should_require_evidence = True
                break
        
        if should_require_evidence:
            step["evidence_required"] = True
            
        # Enforce max revisions
        revisions = step.get("revisions", [])
        if len(revisions) > max_revisions:
            # Mark verification as UNKNOWN and add issue
            if "verification" not in step or step["verification"] is None:
                # Create a dummy verification if missing, or just skip?
                # If it's missing, we can't mark it UNKNOWN easily without structure.
                # But usually verification exists if revisions happened.
                pass
            else:
                step["verification"]["result"] = "UNKNOWN"
                current_notes = step["verification"].get("notes", "")
                step["verification"]["notes"] = (
                    f"{current_notes}; Max revisions ({max_revisions}) exceeded."
                ).strip("; ")


def compute_final_confidence(
    policy: Dict[str, Any],
    domain: str,
    base_confidence: float,
    had_contradiction: bool,
    had_revision: bool
) -> float:
    """
    Computes the final confidence score based on policy penalties.
    
    Args:
        policy: The loaded policy dictionary.
        domain: The domain of the task.
        base_confidence: The initial confidence score.
        had_contradiction: Whether a contradiction was detected.
        had_revision: Whether a revision occurred.
        
    Returns:
        The adjusted confidence score (0.0 to 1.0).
    """
    domain_defaults = policy.get("domain_defaults", {}).get(domain, {})
    contradiction_penalty = domain_defaults.get("contradiction_penalty", 0.0)
    revision_penalty = domain_defaults.get("revision_penalty", 0.0)
    
    confidence = base_confidence
    
    if had_contradiction:
        confidence -= contradiction_penalty
        
    if had_revision:
        confidence -= revision_penalty
        
    return max(0.0, min(1.0, confidence))


def enforce_finalization_policy(
    policy: Dict[str, Any],
    domain: str,
    final_conclusion: Dict[str, Any],
    steps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Enforces finalization rules, potentially blocking the output.
    
    Args:
        policy: The loaded policy dictionary.
        domain: The domain of the task.
        final_conclusion: The proposed final conclusion dictionary.
        steps: List of step dictionaries.
        
    Returns:
        The potentially modified final conclusion dictionary.
    """
    domain_defaults = policy.get("domain_defaults", {}).get(domain, {})
    global_rules = policy.get("global_rules", {})
    
    fail_closed = domain_defaults.get("fail_closed_if_unverified", False)
    min_confidence = domain_defaults.get("min_confidence_to_finalize", 0.0)
    global_block_threshold = global_rules.get("block_if_confidence_below", 0.0)
    block_message = global_rules.get("block_message", "Output blocked by policy.")
    
    should_block = False
    block_reason = ""
    
    # Check fail_closed_if_unverified
    if fail_closed:
        for step in steps:
            verification = step.get("verification")
            if not verification:
                 if step.get("evidence_required", False):
                     should_block = True
                     block_reason = f"Step {step.get('step_index', '?')} missing verification."
                     break
                 continue
            
            status = verification.get("result", "UNKNOWN")
            
            # Block if UNKNOWN (policy violation) or if WEAK and evidence required
            if status == "UNKNOWN":
                should_block = True
                step_display_id = f"S{step.get('step_index', 0) + 1}"
                step_action = step.get('action', 'Unknown Action')
                block_reason = f"Step {step_display_id} {step_action} is UNKNOWN (Policy Violation)."
                break
                
            if status == "WEAK" and step.get("evidence_required", False):
                should_block = True
                step_display_id = f"S{step.get('step_index', 0) + 1}"
                step_action = step.get('action', 'Unknown Action')
                block_reason = f"Step {step_display_id} {step_action} is WEAK."
                break
    
    current_confidence = final_conclusion.get("confidence", 0.0)
    
    # Check min_confidence_to_finalize
    if not should_block and current_confidence < min_confidence:
        should_block = True
        block_reason = f"Confidence {current_confidence:.2f} is below domain minimum {min_confidence:.2f}."
        
    # Check global block_if_confidence_below
    if not should_block and current_confidence < global_block_threshold:
        should_block = True
        block_reason = f"Confidence {current_confidence:.2f} is below global threshold {global_block_threshold:.2f}."
        
    if should_block:
        final_conclusion["content"] = f"{block_message} Reason: {block_reason}"
        final_conclusion["confidence"] = 0.0
        # Add note about blocking
        # There isn't a standard field for this in final_conclusion, 
        # but we can append to content or just leave it as the content override.
        # The prompt says: "Override final_conclusion.content with policy block message plus short reason"
        # "Set final_conclusion.confidence = 0.0"
        # "Add a note that policy blocked finalization" -> Maybe in audit logs? 
        # But this function returns final_conclusion.
        # I'll stick to modifying final_conclusion.
        
    return final_conclusion
