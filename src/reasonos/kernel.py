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
from .policy.policy_loader import load_policy
from .policy.policy_engine import (
    apply_step_policy,
    compute_final_confidence,
    enforce_finalization_policy,
)
from .routing.router import resolve_and_attach_executor
from .executors import gpt_stub, o3_stub, retriever_stub


KERNEL_VERSION = "0.1.0"
RSL_VERSION = "0.1"


def run_demo_task(policy_path: str = "policies/default_policy.json") -> dict[str, Any]:
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

    # Load policy
    policy = load_policy(policy_path)

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
    # Apply policy before verification
    apply_step_policy(policy, "finance", [s1, s2])

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
    # Compute final confidence
    final_conf = compute_final_confidence(
        policy, "finance", 0.95, had_contradiction=False, had_revision=False
    )

    final_conclusion = build_final_conclusion(
        content=f"The monthly payment for the loan is approximately {payment_value} dollars.",
        confidence=final_conf,
        supported_step_ids=[s1_id, s2_id],
        unresolved_contradictions=[],
        finalized_at=ended_at,
    )

    # Enforce finalization policy
    final_conclusion = enforce_finalization_policy(
        policy, "finance", final_conclusion, [s1, s2]
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
    memory_path: str | None = None,
    policy_path: str = "policies/default_policy.json",
) -> dict[str, Any]:
    """
    Run the paper verification task with optional memory integration.

    Verifies a claim paragraph against evidence from a document.
    When memory_path is provided, reads prior memory, detects contradictions,
    and writes new memory facts.

    Pipeline:
        1. S1: Extract the primary claim from the paragraph
        2. S2: Retrieve evidence snippets from the document
        3. S3: Verify whether the evidence supports the claim
        4. Revision: If contradicted, rewrite claim and update S1

    Args:
        paragraph: The paragraph containing the claim to verify.
        document_path: Path to the document file.
        memory_path: Optional path to memory JSON file for persistence.

    Returns:
        A complete RSL document dictionary ready for validation and output.

    Raises:
        FileNotFoundError: If the document file does not exist.
    """
    import re
    from pathlib import Path
    from .evidence.sentence_retriever import retrieve_evidence
    from .utils.ids import new_memory_id, new_revision_id
    from .storage.memory_store import load_memory, append_memory
    from .consistency.contradiction_detector import (
        detect_numeric_contradictions,
        extract_percent,
    )
    from .revision.revision_engine import rewrite_claim

    # Read document
    doc_path = Path(document_path)
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    document_text = doc_path.read_text(encoding="utf-8")

    # === Load prior memory if path provided ===
    prior_memory = []
    if memory_path:
        prior_memory = load_memory(memory_path)

    # Load policy
    policy = load_policy(policy_path)

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
        executor={"type": "MODEL", "name": "unrouted", "config": {}},
        evidence_required=False,
        evidence=[],
    )
    s1["revisions"] = []  # Initialize revisions array

    # Route executor
    resolve_and_attach_executor(policy, "research_verification", s1)

    # Execute S1
    if s1["executor"]["name"] == "gpt_stub":
        s1_context = {"inputs": {"paragraph": paragraph}}
        s1_output = gpt_stub.execute(s1, s1_context)
    else:
        # Fallback or other executors
        s1_output = paragraph

    s1["status"] = "EXECUTED"
    s1["ended_at"] = now_iso()
    s1["execution_output"] = s1_output
    s1["execution"] = {"executor_used": s1["executor"]["name"]}

    # Verify S1
    apply_step_policy(policy, "research_verification", [s1])
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
        executor={"type": "MODEL", "name": "unrouted", "config": {}},
        evidence_required=True,
        evidence=[],
    )

    # Route executor
    resolve_and_attach_executor(policy, "research_verification", s2)

    # Execute S2
    s2_context = {
        "inputs": {"paragraph": paragraph},
        "document_text": document_text
    }
    
    if s2["executor"]["name"] == "retriever_stub":
        retriever_result = retriever_stub.execute(s2, s2_context)
        evidence_results = retriever_result["retrieved_evidence"]
        s2_output = retriever_result["summary"]
    else:
        # Fallback to direct tool call if not routed to stub (should not happen in demo)
        evidence_results = retrieve_evidence(paragraph, document_text, k=3)
        s2_output = f"Retrieved {len(evidence_results)} evidence sentences"

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
    s2["execution_output"] = s2_output
    s2["evidence"] = s2_evidence
    s2["execution"] = {"executor_used": s2["executor"]["name"]}

    # Verify S2
    apply_step_policy(policy, "research_verification", [s2])
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
        executor={"type": "MODEL", "name": "unrouted", "config": {}},
        evidence_required=True,
        evidence=[],
    )

    # Route executor
    resolve_and_attach_executor(policy, "research_verification", s3)

    # Verify S3
    apply_step_policy(policy, "research_verification", [s3])

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
    
    if s3["executor"]["name"] == "o3_stub":
        # O3 stub returns analysis, but we still need verification status from rule verifier
        o3_output = o3_stub.execute(s3, {})
        s3["execution_output"] = f"{o3_output} | Verification result: {verification_status}"
    else:
        s3["execution_output"] = f"Verification result: {verification_status}"
        
    s3["evidence"] = s3_evidence
    s3["execution"] = {"executor_used": s3["executor"]["name"]}

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

    # === Revision Logic ===
    revision_triggered = False
    if verification_status == "CONTRADICTED":
        # Attempt to rewrite claim
        rewritten_claim = rewrite_claim(paragraph, evidence_sentences)
        
        if rewritten_claim != paragraph:
            revision_triggered = True
            revised_at = now_iso()
            revision_id = new_revision_id()
            
            # Create revision record
            new_verification = build_verification(
                result="SUPPORTED",
                confidence=min(verification_confidence + 0.3, 0.9),
                checked_evidence_ids=s3_checked_evidence_ids,
                verified_at=revised_at,
                notes="Claim rewritten to match verified evidence",
            )
            
            revision_record = {
                "revision_id": revision_id,
                "reason": "Original claim contradicted by evidence",
                "action": "REWRITE_CLAIM_TO_MATCH_EVIDENCE",
                "previous_verification_status": "CONTRADICTED",
                "new_execution_output": rewritten_claim,
                "new_verification": new_verification,
                "revised_at": revised_at,
            }
            
            # Update S1
            s1["revisions"].append(revision_record)
            s1["execution_output"] = rewritten_claim
            s1["verification"] = new_verification
            
            # Update S3 to reflect the new reality
            verification_status = "SUPPORTED"
            verification_confidence = new_verification["confidence"]
            issues = ["Claim rewritten to match verified evidence"]
            
            s3["verification"] = build_verification(
                result="SUPPORTED",
                confidence=verification_confidence,
                checked_evidence_ids=s3_checked_evidence_ids,
                verified_at=revised_at,
                notes="Claim revised to match evidence",
            )
            s3["execution_output"] = "Verification result: SUPPORTED (after revision)"
            
            # Update local claim variable for downstream logic
            claim = rewritten_claim
            paragraph = rewritten_claim # Update paragraph so extract_percent works on revised claim

    # === Contradiction detection ===
    contradictions = []
    if memory_path and prior_memory:
        # Extract percent from current claim (revised if applicable)
        claim_percent = extract_percent(paragraph)
        if claim_percent is not None:
            contradictions = detect_numeric_contradictions(
                memory_items=prior_memory,
                current_subject="Model X Dataset Y",
                current_value=claim_percent,
                unit="%",
                threshold=0.5,
            )

    # === Build memory writes ===
    memory_writes = []
    if memory_path and verification_status in ("SUPPORTED", "PARTIALLY_SUPPORTED"):
        # Build a normalized fact from evidence
        # Use the first evidence sentence as the primary fact
        if evidence_sentences:
            fact_content = evidence_sentences[0]
        else:
            fact_content = paragraph

        memory_write = {
            "memory_id": new_memory_id(),
            "type": "FACT",
            "content": fact_content,
            "confidence": verification_confidence,
            "derived_from_step_ids": [s2_id, s3_id],
            "written_at": now_iso(),
        }
        memory_writes.append(memory_write)

    # === Finalize run ===
    ended_at = now_iso()
    run["status"] = "FINALIZED"
    run["ended_at"] = ended_at

    # === Create final conclusion with readable format ===
    # Extract evidence percent and scope info from issues
    evidence_percent = None
    scope_info = None
    claim_percent = extract_percent(paragraph) if memory_path else None

    for issue in issues:
        if "evidence shows" in issue:
            match = re.search(r"evidence shows (\d+\.?\d*)%", issue)
            if match:
                evidence_percent = match.group(1)
        if "Scope limitation" in issue:
            match = re.search(r"'([^']+)'", issue)
            if match:
                scope_info = match.group(1)

    # Adjust confidence if contradictions detected
    final_confidence = verification_confidence
    if contradictions:
        final_confidence = max(0.0, min(1.0, verification_confidence - 0.25))

    # Apply policy to confidence
    final_confidence = compute_final_confidence(
        policy,
        "research_verification",
        final_confidence,
        had_contradiction=bool(contradictions),
        had_revision=revision_triggered,
    )

    # Build conclusion based on verification status and contradictions
    if revision_triggered:
        conclusion_content = (
            f"The original claim was revised after contradiction. "
            f"The corrected claim states that {paragraph} "
            f"Confidence: {final_confidence:.2f}."
        )
    elif contradictions and verification_status == "WEAK":
        # Primary reason is document contradiction, memory is secondary
        prior_val = contradictions[0]["prior_value"]
        curr_val = contradictions[0]["current_value"]
        conclusion_content = (
            f"The claim is CONTRADICTED by the document, which reports {evidence_percent or prior_val}% "
            f"rather than {curr_val}%. "
            f"This also conflicts with prior memory recorded from earlier verified runs. "
            f"Confidence: {final_confidence:.2f}."
        )
    elif contradictions:
        # Has contradictions but not WEAK status
        prior_val = contradictions[0]["prior_value"]
        curr_val = contradictions[0]["current_value"]
        conclusion_content = (
            f"The claim is PARTIALLY SUPPORTED but conflicts with prior memory. "
            f"The document reports {evidence_percent or prior_val}%, "
            f"which differs from the claimed {curr_val}%. "
            f"Confidence: {final_confidence:.2f}."
        )
    elif verification_status == "SUPPORTED":
        conclusion_content = (
            f"The claim is SUPPORTED by the evidence. "
            f"The document confirms the stated improvement. "
            f"Confidence: {final_confidence:.2f}."
        )
    elif verification_status == "PARTIALLY_SUPPORTED":
        if evidence_percent and scope_info:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence reports {evidence_percent}% {scope_info}, "
                f"which is close to the claimed value but not identical "
                f"and does not generalize beyond that scope. "
                f"Confidence: {final_confidence:.2f}."
            )
        elif evidence_percent:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence reports {evidence_percent}%, "
                f"which differs slightly from the claimed value. "
                f"Confidence: {final_confidence:.2f}."
            )
        elif scope_info:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"The evidence is limited to {scope_info} "
                f"and may not generalize beyond that scope. "
                f"Confidence: {final_confidence:.2f}."
            )
        else:
            conclusion_content = (
                f"The claim is PARTIALLY SUPPORTED. "
                f"Some aspects of the claim could not be fully verified. "
                f"Confidence: {final_confidence:.2f}."
            )
    else:
        conclusion_content = (
            f"The claim has WEAK support. "
            f"The evidence does not adequately support the stated claim. "
            f"Confidence: {final_confidence:.2f}."
        )

    # Append contradiction notice if detected
    if contradictions:
        conclusion_content += (
            " WARNING: This claim conflicts with prior memory. "
            f"A numeric discrepancy of {abs(contradictions[0]['current_value'] - contradictions[0]['prior_value']):.1f}% was detected."
        )

    # Add CONTRADICTION memory write if contradictions detected
    if memory_path and contradictions:
        for c in contradictions:
            contradiction_memory = {
                "memory_id": new_memory_id(),
                "type": "CONTRADICTION",
                "content": c["description"],
                "confidence": 0.90,
                "derived_from_step_ids": [s3_id],
                "written_at": now_iso(),
            }
            memory_writes.append(contradiction_memory)

    final_conclusion = build_final_conclusion(
        content=conclusion_content,
        confidence=final_confidence,
        supported_step_ids=[s1_id, s2_id, s3_id],
        unresolved_contradictions=[c["contradiction_id"] for c in contradictions],
        finalized_at=ended_at,
    )

    # Re-apply policy to catch any revision violations
    apply_step_policy(policy, "research_verification", [s1, s2, s3])

    # Enforce finalization policy
    final_conclusion = enforce_finalization_policy(
        policy, "research_verification", final_conclusion, [s1, s2, s3]
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

    if revision_triggered:
        audit_logs.append({
            "event": "REVISION_TRIGGERED",
            "timestamp": now_iso(),
            "details": {
                "step_id": s1_id,
                "reason": "Original claim contradicted by evidence",
            },
        })

    if contradictions:
        audit_logs.append({
            "event": "CONTRADICTION_DETECTED",
            "timestamp": now_iso(),
            "details": {
                "count": len(contradictions),
                "severity": "HIGH",
                "contradiction_ids": [c["contradiction_id"] for c in contradictions],
                "threshold_used": 0.5,
            },
        })

    if memory_writes:
        audit_logs.append({
            "event": "MEMORY_WRITTEN",
            "timestamp": now_iso(),
            "details": {
                "count": len(memory_writes),
                "types": list(set(m["type"] for m in memory_writes)),
            },
        })

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
        "contradictions": contradictions,
        "final_conclusion": final_conclusion,
        "memory_writes": memory_writes,
        "audit": audit,
    }

    # === Persist memory writes ===
    if memory_path and memory_writes:
        append_memory(memory_path, memory_writes)

    return rsl_document


