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
)
from .utils.ids import new_task_id, new_run_id, new_step_id, new_evidence_id
from .utils.time import now_iso
from .executors import model_executor, tool_executor
from .verifiers.rule_verifier import verify_step


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
