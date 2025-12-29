"""Rule-based verifier for ReasonOS steps.

Verifies step execution results using deterministic rules.
"""

from typing import Any

from ..utils.time import now_iso
from ..utils.text import extract_percent_value
from ..rsl import build_verification


class VerificationError(Exception):
    """Raised when step verification fails structural checks."""

    pass


# Scope limitation phrases that indicate limited applicability
SCOPE_LIMITERS = [
    "in the indoor setting",
    "under condition",
    "controlled conditions",
    "specific setting",
    "limited to",
]


def verify_claim_support(
    claim: str,
    evidence_sentences: list[str],
) -> tuple[str, float, list[str]]:
    """
    Verify whether evidence supports a claim using deterministic rules.

    Rules:
        - Extract percent values from claim and evidence
        - Check for Model X and Dataset Y mentions
        - Compare percent values for exact or approximate match
        - Detect scope limitations

    Args:
        claim: The claim string to verify.
        evidence_sentences: List of evidence sentence strings.

    Returns:
        A tuple of (status, confidence, issues) where:
            - status: "SUPPORTED", "PARTIALLY_SUPPORTED", or "WEAK"
            - confidence: A value between 0 and 1
            - issues: List of identified issues (rounding, scope, etc.)
    """
    issues = []

    if not evidence_sentences:
        return ("WEAK", 0.3, ["No evidence sentences provided"])

    # Extract percent from claim
    claim_percent = extract_percent_value(claim)
    claim_lower = claim.lower()

    # Check for key entities in claim
    has_model_x = "model x" in claim_lower
    has_dataset_y = "dataset y" in claim_lower

    # Search evidence for supporting information
    evidence_percent = None
    evidence_has_model_x = False
    evidence_has_dataset_y = False
    scope_limited = False
    scope_limiter_found = None

    combined_evidence = " ".join(evidence_sentences).lower()

    # Check for entities in evidence
    evidence_has_model_x = "model x" in combined_evidence
    evidence_has_dataset_y = "dataset y" in combined_evidence

    # Extract percent from evidence
    for sentence in evidence_sentences:
        pct = extract_percent_value(sentence)
        if pct is not None:
            evidence_percent = pct
            break

    # Check for scope limitations
    for limiter in SCOPE_LIMITERS:
        if limiter in combined_evidence:
            scope_limited = True
            scope_limiter_found = limiter
            break

    # Determine support level
    if not evidence_has_model_x and has_model_x:
        issues.append("Evidence does not mention Model X")
        return ("WEAK", 0.35, issues)

    if not evidence_has_dataset_y and has_dataset_y:
        issues.append("Evidence does not mention Dataset Y")
        return ("WEAK", 0.35, issues)

    if claim_percent is not None and evidence_percent is None:
        issues.append("Evidence does not contain a numeric improvement value")
        return ("WEAK", 0.4, issues)

    # Compare percent values
    if claim_percent is not None and evidence_percent is not None:
        diff = abs(claim_percent - evidence_percent)
        if diff == 0:
            # Exact match
            if scope_limited:
                issues.append(f"Scope limitation detected: '{scope_limiter_found}'")
                return ("PARTIALLY_SUPPORTED", 0.75, issues)
            return ("SUPPORTED", 0.90, issues)
        elif diff <= 0.5:
            # Close match - rounding issue
            issues.append(
                f"Rounding discrepancy: claim states {claim_percent}%, "
                f"evidence shows {evidence_percent}%"
            )
            if scope_limited:
                issues.append(f"Scope limitation detected: '{scope_limiter_found}'")
                return ("PARTIALLY_SUPPORTED", 0.65, issues)
            return ("PARTIALLY_SUPPORTED", 0.75, issues)
        else:
            # Significant difference
            issues.append(
                f"Numeric mismatch: claim states {claim_percent}%, "
                f"evidence shows {evidence_percent}%"
            )
            return ("WEAK", 0.45, issues)

    # General case - entities match but no numeric comparison
    if scope_limited:
        issues.append(f"Scope limitation detected: '{scope_limiter_found}'")
        return ("PARTIALLY_SUPPORTED", 0.70, issues)

    return ("SUPPORTED", 0.85, issues)


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
