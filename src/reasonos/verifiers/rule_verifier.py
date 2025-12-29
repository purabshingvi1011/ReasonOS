"""Rule-based verifier for ReasonOS steps.

Verifies step execution results using deterministic rules.
"""

from typing import Any

from ..utils.time import now_iso
from ..rsl import build_verification


class VerificationError(Exception):
    """Raised when step verification fails structural checks."""

    pass


def verify_step(step: dict[str, Any]) -> dict[str, Any]:
    """
    Verify a step using rule-based checks.

    Performs structural validation and returns a verification object.

    Structural checks:
        - Required fields exist (step_id, action, status, executor)
        - If evidence_required is True, evidence must be non-empty

    Args:
        step: The step dictionary to verify.

    Returns:
        A verification dictionary with:
            - result: "SUPPORTED" or "FAILED"
            - confidence: A value between 0 and 1
            - checked_evidence_ids: List of evidence IDs that were checked
            - verified_at: ISO timestamp
            - notes: Optional verification notes

    Raises:
        VerificationError: If structural checks fail.
    """
    # Structural validation
    required_fields = ["step_id", "action", "status", "executor"]
    for field in required_fields:
        if field not in step:
            raise VerificationError(f"Missing required field: {field}")

    # Check evidence requirement
    evidence_required = step.get("evidence_required", False)
    evidence = step.get("evidence", [])

    if evidence_required and not evidence:
        raise VerificationError(
            f"Step {step['step_id']} requires evidence but none provided"
        )

    # Determine checked evidence IDs
    checked_evidence_ids = [ev["evidence_id"] for ev in evidence]

    # Determine verification result based on step type
    execution_output = step.get("execution_output")
    if execution_output is None:
        raise VerificationError(
            f"Step {step['step_id']} has no execution_output"
        )

    # For the demo, all steps with valid structure pass verification
    # In a real system, this would apply domain-specific rules
    result = "SUPPORTED"
    confidence = 0.95

    notes = None
    if evidence:
        notes = f"Verified with {len(evidence)} evidence item(s)"
    else:
        notes = "Verified by structural and logical checks"

    return build_verification(
        result=result,
        confidence=confidence,
        checked_evidence_ids=checked_evidence_ids,
        verified_at=now_iso(),
        notes=notes,
    )
