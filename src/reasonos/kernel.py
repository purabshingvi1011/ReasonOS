"""ReasonOS microkernel orchestrator.

Coordinates task execution, step processing, verification, and RSL document assembly.
"""

from typing import Any

from .rsl import (
    build_task,
    build_run,
    build_step,
    build_evidence,
    build_final_conclusion,
    build_audit,
    build_verification,
)
from .utils.ids import new_task_id, new_run_id, new_step_id, new_evidence_id
from .utils.time import now_iso
from .executors import model_executor, tool_executor
from .verifiers.rule_verifier import verify_step, verify_claim_support


KERNEL_VERSION = "0.1.0"
RSL_VERSION = "0.1"


def run_demo_task() -> dict[str, Any]:
    """
    Run the demo loan payment calculation task.

    Orchestrates the full ReasonOS pipeline:
        1. Create task and run objects
        2. Create S1 (formula selection) and S2 (calculation) steps
        3. Execute S1 using model_executor
        4. Execute S2 using tool_executor, create evidence E1
        5. Verify S1 and S2 using rule_verifier
        6. Finalize run status
        7. Assemble full RSL document

    Returns:
        A complete RSL document dictionary ready for validation and output.
    """
    # Demo task parameters
    demo_objective = (
        "What is the monthly payment for a 10000 dollar loan "
        "at 5 percent annual interest for 3 years?"
    )
    demo_inputs = {
        "principal": 10000,
        "annual_rate": 0.05,
        "months": 36,
    }

    # === Step 1: Create task and run ===
    task_id = new_task_id()
    run_id = new_run_id()
    started_at = now_iso()

    task = build_task(
        task_id=task_id,
        objective=demo_objective,
        domain="finance",
        created_at=started_at,
        inputs=demo_inputs,
    )

    run = build_run(
        run_id=run_id,
        status="RUNNING",
        started_at=started_at,
        model_policy={"provider": "stub", "model": "deterministic"},
        tool_policy={"allowed_tools": ["calculator"]},
    )

    # === Step 2: Create S1 step (formula selection) ===
    s1_id = new_step_id()
    s1_started = now_iso()

    s1 = build_step(
        step_id=s1_id,
        step_index=0,
        action="Select the appropriate formula for calculating loan payments",
        status="PENDING",
        started_at=s1_started,
        ended_at=s1_started,  # Will be updated after execution
        depends_on=[],
        executor="model",
        evidence_required=False,
        evidence=[],
    )

    # === Step 3: Execute S1 ===
    s1_context = {"task": task, "inputs": demo_inputs}
    s1_output = model_executor.execute(s1, s1_context)
    s1_ended = now_iso()

    # Update S1 with execution results
    s1["status"] = "EXECUTED"
    s1["ended_at"] = s1_ended
    s1["execution_output"] = s1_output

    # === Step 4: Create S2 step (payment calculation) ===
    s2_id = new_step_id()
    s2_started = now_iso()

    s2 = build_step(
        step_id=s2_id,
        step_index=1,
        action="Calculate the monthly payment using the amortized loan formula",
        status="PENDING",
        started_at=s2_started,
        ended_at=s2_started,  # Will be updated after execution
        depends_on=[s1_id],
        executor="tool",
        evidence_required=True,
        evidence=[],
    )

    # === Step 5: Execute S2 and create evidence ===
    s2_context = demo_inputs.copy()
    s2_result = tool_executor.execute(s2, s2_context)
    s2_ended = now_iso()

    # Create evidence from tool output
    e1_id = new_evidence_id()
    evidence_e1 = build_evidence(
        evidence_id=e1_id,
        source="calculator_tool",
        content={
            "tool_call_id": s2_result["tool_call_id"],
            "monthly_payment": s2_result["payment_value"],
            "formatted": s2_result["payment_display"],
            "inputs": {
                "principal": demo_inputs["principal"],
                "annual_rate": demo_inputs["annual_rate"],
                "months": demo_inputs["months"],
            },
        },
        created_at=s2_ended,
    )

    # Update S2 with execution results and evidence
    s2["status"] = "EXECUTED"
    s2["ended_at"] = s2_ended
    s2["execution_output"] = f"Calculated payment: {s2_result['payment_display']}"
    s2["evidence"] = [evidence_e1]

    # === Step 6: Verify S1 and S2 ===
    s1_verification = verify_step(s1)
    s1["verification"] = s1_verification
    s1["status"] = "VERIFIED"

    s2_verification = verify_step(s2)
    s2["verification"] = s2_verification
    s2["status"] = "VERIFIED"

    # === Step 7: Finalize run ===
    ended_at = now_iso()
    run["status"] = "FINALIZED"
    run["ended_at"] = ended_at

    # === Step 8: Create final conclusion ===
    payment_value = s2_result["payment_value"]
    final_conclusion = build_final_conclusion(
        content=f"The monthly payment for the loan is approximately {payment_value} dollars.",
        confidence=0.95,
        supported_step_ids=[s1_id, s2_id],
        unresolved_contradictions=[],
        finalized_at=ended_at,
    )

    # === Step 9: Assemble full RSL document ===
    audit = build_audit(
        kernel_version=KERNEL_VERSION,
        rsl_version=RSL_VERSION,
        logs=[],
    )

    rsl_document = {
        "rsl_version": RSL_VERSION,
        "task": task,
        "run": run,
        "steps": [s1, s2],
        "contradictions": [],
        "final_conclusion": final_conclusion,
        "memory_writes": [],
        "audit": audit,
    }

    return rsl_document


def run_paper_verification_task(
    paragraph: str,
    document_path: str,
) -> dict[str, Any]:
    """
    Run the paper verification task.

    Verifies a claim paragraph against evidence from a document.

    Pipeline:
        1. S1: Extract the primary claim from the paragraph
        2. S2: Retrieve evidence snippets from the document
        3. S3: Verify whether the evidence supports the claim

    Args:
        paragraph: The paragraph containing the claim to verify.
        document_path: Path to the document file.

    Returns:
        A complete RSL document dictionary ready for validation and output.

    Raises:
        FileNotFoundError: If the document file does not exist.
    """
    from pathlib import Path
    from .evidence.sentence_retriever import retrieve_evidence

    # Read document
    doc_path = Path(document_path)
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    document_text = doc_path.read_text(encoding="utf-8")

    # === Create task and run ===
    task_id = new_task_id()
    run_id = new_run_id()
    started_at = now_iso()

    task = build_task(
        task_id=task_id,
        objective="Verify the claim against the provided document",
        domain="research_verification",
        created_at=started_at,
        inputs={
            "paragraph": paragraph,
            "document_path": document_path,
        },
    )

    run = build_run(
        run_id=run_id,
        status="RUNNING",
        started_at=started_at,
        model_policy={"provider": "stub", "model": "deterministic"},
        tool_policy={"allowed_tools": ["sentence_retriever"]},
    )

    # === Step S1: Extract the primary claim ===
    s1_id = new_step_id()
    s1_started = now_iso()

    s1 = build_step(
        step_id=s1_id,
        step_index=0,
        action="Extract the primary claim from the paragraph",
        status="PENDING",
        started_at=s1_started,
        ended_at=s1_started,
        depends_on=[],
        executor="model",
        evidence_required=False,
        evidence=[],
    )

    # Execute S1 - for determinism, output is the paragraph itself
    s1["status"] = "EXECUTED"
    s1["ended_at"] = now_iso()
    s1["execution_output"] = paragraph

    # Verify S1
    s1_verification = verify_step(s1)
    s1["verification"] = s1_verification
    s1["status"] = "VERIFIED"

    # === Step S2: Retrieve evidence snippets ===
    s2_id = new_step_id()
    s2_started = now_iso()

    s2 = build_step(
        step_id=s2_id,
        step_index=1,
        action="Retrieve evidence snippets from the document",
        status="PENDING",
        started_at=s2_started,
        ended_at=s2_started,
        depends_on=[s1_id],
        executor="tool",
        evidence_required=True,
        evidence=[],
    )

    # Execute S2 - retrieve evidence
    evidence_results = retrieve_evidence(paragraph, document_text, k=3)
    s2_ended = now_iso()

    # Create evidence records for S2
    s2_evidence = []
    for idx, ev_result in enumerate(evidence_results):
        ev_id = new_evidence_id()
        evidence_item = build_evidence(
            evidence_id=ev_id,
            source="sentence_retriever",
            content={
                "sentence": ev_result["content"],
                "relevance_score": ev_result["relevance_score"],
                "sentence_index": ev_result["sentence_index"],
            },
            created_at=s2_ended,
        )
        s2_evidence.append(evidence_item)

    s2["status"] = "EXECUTED"
    s2["ended_at"] = s2_ended
    s2["execution_output"] = f"Retrieved {len(evidence_results)} evidence sentences"
    s2["evidence"] = s2_evidence

    # Verify S2
    s2_verification = verify_step(s2)
    s2["verification"] = s2_verification
    s2["status"] = "VERIFIED"

    # === Step S3: Verify claim support ===
    s3_id = new_step_id()
    s3_started = now_iso()

    s3 = build_step(
        step_id=s3_id,
        step_index=2,
        action="Verify whether the evidence supports the claim",
        status="PENDING",
        started_at=s3_started,
        ended_at=s3_started,
        depends_on=[s1_id, s2_id],
        executor="model",
        evidence_required=True,
        evidence=[],
    )

    # Execute S3 - use the same evidence from S2
    evidence_sentences = [ev["content"]["sentence"] for ev in s2_evidence]
    claim = paragraph

    # Perform claim verification
    verification_status, verification_confidence, issues = verify_claim_support(
        claim, evidence_sentences
    )

    s3_ended = now_iso()

    # Create evidence records for S3 (reuse same sentences as S3's own evidence)
    s3_evidence = []
    for ev in s2_evidence:
        # Create new evidence IDs for S3's evidence
        ev_id = new_evidence_id()
        evidence_item = build_evidence(
            evidence_id=ev_id,
            source="claim_verification",
            content={
                "sentence": ev["content"]["sentence"],
                "relevance_score": ev["content"]["relevance_score"],
                "verification_issues": issues,
            },
            created_at=s3_ended,
        )
        s3_evidence.append(evidence_item)

    s3["status"] = "EXECUTED"
    s3["ended_at"] = s3_ended
    s3["execution_output"] = f"Verification result: {verification_status}"
    s3["evidence"] = s3_evidence

    # Build S3 verification using the claim verification results
    s3_checked_evidence_ids = [ev["evidence_id"] for ev in s3_evidence]
    s3["verification"] = build_verification(
        result=verification_status,
        confidence=verification_confidence,
        checked_evidence_ids=s3_checked_evidence_ids,
        verified_at=now_iso(),
        notes="; ".join(issues) if issues else "No issues detected",
    )
    s3["status"] = "VERIFIED"

    # === Finalize run ===
    ended_at = now_iso()
    run["status"] = "FINALIZED"
    run["ended_at"] = ended_at

    # === Create final conclusion with readable format ===
    # Build issue description dynamically based on detected issues
    issue_parts = []
    evidence_percent = None
    scope_info = None

    for issue in issues:
        if "evidence shows" in issue:
            # Extract the evidence percent from the issue string
            import re
            match = re.search(r"evidence shows (\d+\.?\d*)%", issue)
            if match:
                evidence_percent = match.group(1)
        if "Scope limitation" in issue:
            # Extract scope info
            match = re.search(r"'([^']+)'", issue)
            if match:
                scope_info = match.group(1)

    if verification_status == "SUPPORTED":
        conclusion_content = (
            f"The claim is SUPPORTED by the evidence. "
            f"The document confirms the stated improvement. "
            f"Confidence: {verification_confidence}."
        )
    elif verification_status == "PARTIALLY_SUPPORTED":
        # Build a natural language summary from the issues
        if evidence_percent and scope_info:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence reports {evidence_percent}% {scope_info}, "
                f"which is close to the claimed value but not identical "
                f"and does not generalize beyond that scope. "
                f"Confidence: {verification_confidence}."
            )
        elif evidence_percent:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence reports {evidence_percent}%, "
                f"which differs slightly from the claimed value. "
                f"Confidence: {verification_confidence}."
            )
        elif scope_info:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence is limited to {scope_info} "
                f"and may not generalize beyond that scope. "
                f"Confidence: {verification_confidence}."
            )
        else:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"Some aspects of the claim could not be fully verified. "
                f"Confidence: {verification_confidence}."
            )
    else:
        conclusion_content = (
            f"The claim has WEAK support. "
            f"The evidence does not adequately support the stated claim. "
            f"Confidence: {verification_confidence}."
        )

    final_conclusion = build_final_conclusion(
        content=conclusion_content,
        confidence=verification_confidence,
        supported_step_ids=[s1_id, s2_id, s3_id],
        unresolved_contradictions=[],
        finalized_at=ended_at,
    )

    # === Build audit logs ===
    audit_logs = [
        {
            "event": "EVIDENCE_RETRIEVED",
            "timestamp": s2_ended,
            "details": {
                "sentence_count": len(evidence_results),
                "step_id": s2_id,
            },
        },
        {
            "event": "VERIFICATION_COMPLETED",
            "timestamp": s3_ended,
            "details": {
                "status": verification_status,
                "confidence": verification_confidence,
                "step_id": s3_id,
            },
        },
    ]

    # === Assemble full RSL document ===
    audit = build_audit(
        kernel_version=KERNEL_VERSION,
        rsl_version=RSL_VERSION,
        logs=audit_logs,
    )

    rsl_document = {
        "rsl_version": RSL_VERSION,
        "task": task,
        "run": run,
        "steps": [s1, s2, s3],
        "contradictions": [],
        "final_conclusion": final_conclusion,
        "memory_writes": [],
        "audit": audit,
    }

    return rsl_document
