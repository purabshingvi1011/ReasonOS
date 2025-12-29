"""RSL entity builder functions.

Pure functions that build dictionaries for each RSL entity.
These functions do not perform I/O; they only assemble data.
"""

from typing import Any


def build_task(
    task_id: str,
    objective: str,
    domain: str,
    created_at: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Build a task dictionary."""
    return {
        "task_id": task_id,
        "objective": objective,
        "domain": domain,
        "created_at": created_at,
        "inputs": inputs,
    }


def build_run(
    run_id: str,
    status: str,
    started_at: str,
    ended_at: str | None = None,
    model_policy: dict[str, Any] | None = None,
    tool_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a run dictionary."""
    run = {
        "run_id": run_id,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
    }
    if model_policy is not None:
        run["model_policy"] = model_policy
    if tool_policy is not None:
        run["tool_policy"] = tool_policy
    return run


def build_step(
    step_id: str,
    step_index: int,
    action: str,
    status: str,
    started_at: str,
    ended_at: str,
    depends_on: list[str],
    executor: str,
    evidence_required: bool,
    evidence: list[dict[str, Any]],
    execution_output: str | None = None,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a step dictionary."""
    step = {
        "step_id": step_id,
        "step_index": step_index,
        "action": action,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
        "depends_on": depends_on,
        "executor": executor,
        "evidence_required": evidence_required,
        "evidence": evidence,
    }
    if execution_output is not None:
        step["execution_output"] = execution_output
    if verification is not None:
        step["verification"] = verification
    return step


def build_evidence(
    evidence_id: str,
    source: str,
    content: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    """Build an evidence dictionary."""
    return {
        "evidence_id": evidence_id,
        "source": source,
        "content": content,
        "created_at": created_at,
    }


def build_verification(
    result: str,
    confidence: float,
    checked_evidence_ids: list[str],
    verified_at: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a verification dictionary."""
    verification = {
        "result": result,
        "confidence": confidence,
        "checked_evidence_ids": checked_evidence_ids,
        "verified_at": verified_at,
    }
    if notes is not None:
        verification["notes"] = notes
    return verification


def build_final_conclusion(
    content: str,
    confidence: float,
    supported_step_ids: list[str],
    unresolved_contradictions: list[str],
    finalized_at: str,
) -> dict[str, Any]:
    """Build a final conclusion dictionary."""
    return {
        "content": content,
        "confidence": confidence,
        "supported_step_ids": supported_step_ids,
        "unresolved_contradictions": unresolved_contradictions,
        "finalized_at": finalized_at,
    }


def build_audit(
    kernel_version: str,
    rsl_version: str,
    logs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build an audit dictionary."""
    return {
        "kernel_version": kernel_version,
        "rsl_version": rsl_version,
        "logs": logs,
    }
