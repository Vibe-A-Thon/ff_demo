"""Workflow governance routes.

Manage workflow state transitions and approvals.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.models import WorkflowAdvanceRequest, WorkflowDecisionRequest, WorkflowAutoRunRequest
from app.run_helpers import record_run_event
from app.workflow_service import (
    WORKFLOW_STATES,
    APPROVAL_STATES,
    TERMINAL_WORKFLOW_STATES,
    advance_workflow,
    decide_workflow,
    get_workflow_approvals,
    compute_governance_status,
)
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/workflow/{run_id}")
async def get_workflow(run_id: str, current_user: dict = Depends(require_permission("workflow:read"))) -> Dict[str, Any]:
    """Get workflow state for a run.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Workflow summary.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.read",
        "run",
        run_id,
        metadata={"workflow_state": run.get("workflow_state", "incident_created")},
    )
    return {
        "run_id": run_id,
        "workflow_state": run.get("workflow_state", "incident_created"),
        "workflow_status": run.get("workflow_status", "running"),
        "workflow_history": run.get("workflow_history", []),
        "pending_approval": run.get("pending_approval"),
        "is_terminal": run.get("workflow_state") in TERMINAL_WORKFLOW_STATES,
        "approval_required": run.get("workflow_state") in APPROVAL_STATES,
    }


@router.get("/workflow/{run_id}/approvals")
async def get_workflow_approvals_endpoint(run_id: str, current_user: dict = Depends(require_permission("workflow:read"))) -> Dict[str, Any]:
    """Get approvals for a run workflow.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Approval list.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    approvals = await get_workflow_approvals(run_id)
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.approvals.read",
        "run",
        run_id,
    )
    return {"run_id": run_id, "approvals": approvals}


@router.get("/workflow/{run_id}/status")
async def get_workflow_status(run_id: str, current_user: dict = Depends(require_permission("workflow:read"))) -> Dict[str, Any]:
    """Get governance status for a run.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Governance status summary.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    governance = await compute_governance_status(run_id)
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.status.read",
        "run",
        run_id,
        metadata={"workflow_state": run.get("workflow_state", "incident_created")},
    )
    return {
        "run_id": run_id,
        "workflow_state": run.get("workflow_state", "incident_created"),
        "workflow_status": run.get("workflow_status", "running"),
        "pending_approval": run.get("pending_approval"),
        "governance": governance,
    }

@router.post("/workflow/{run_id}/advance")
async def advance_workflow_state(run_id: str, payload: WorkflowAdvanceRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Advance a workflow state for a run.

    Args:
        run_id: Run identifier.
        payload: Advance request payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Workflow transition result.

    Raises:
        HTTPException: If run is not found or state invalid.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    current_state = run.get("workflow_state", "incident_created")
    if current_state not in WORKFLOW_STATES:
        raise HTTPException(status_code=400, detail="Unknown workflow state")

    if current_state in APPROVAL_STATES:
        await record_audit(
            current_user.get("id", "unknown"),
            "workflow.advance",
            "run",
            run_id,
            decision="awaiting_approval",
            metadata={"state": current_state, "actor_id": payload.actor_id},
        )
        return {
            "run_id": run_id,
            "workflow_state": current_state,
            "status": "awaiting_approval",
        }

    next_state, transitions = await advance_workflow(run, payload.actor_id, payload.outcome, payload.notes)
    if not transitions:
        await record_audit(
            current_user.get("id", "unknown"),
            "workflow.advance",
            "run",
            run_id,
            decision="no_transition",
            metadata={"state": current_state, "actor_id": payload.actor_id, "outcome": payload.outcome},
        )
        return {"run_id": run_id, "workflow_state": current_state, "status": "no_transition"}

    pending_approval = None
    workflow_status = "running"
    if next_state in APPROVAL_STATES:
        workflow_status = "awaiting_approval"
        pending_approval = await db.approvals.find_one(
            {"resource_type": "run", "resource_id": run_id, "action": next_state, "status": "pending"},
            {"_id": 0},
        )

    await record_run_event(run_id, "workflow.state_changed", {"from": current_state, "to": next_state})
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.advance",
        "run",
        run_id,
        metadata={"from": current_state, "to": next_state, "reason": payload.notes},
    )
    logger.info(
        "workflow.state_changed",
        extra={"payload": {"run_id": run_id, "from": current_state, "to": next_state}},
    )
    await db.runs.update_one(
        {"id": run_id},
        {
            "$set": {
                "workflow_state": next_state,
                "workflow_status": "completed" if next_state in TERMINAL_WORKFLOW_STATES else workflow_status,
                "pending_approval": pending_approval,
            },
            "$push": {"workflow_history": {"$each": transitions}},
        },
    )

    return {
        "run_id": run_id,
        "workflow_state": next_state,
        "transitions": transitions,
    }

@router.post("/workflow/{run_id}/decision")
async def decide_workflow_state(run_id: str, payload: WorkflowDecisionRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Record a workflow approval decision.

    Args:
        run_id: Run identifier.
        payload: Decision payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Decision result.

    Raises:
        HTTPException: If run is not found or not awaiting approval.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    current_state = run.get("workflow_state", "incident_created")
    if current_state not in APPROVAL_STATES:
        raise HTTPException(status_code=400, detail="Current state does not require approval")

    next_state, entry = await decide_workflow(run, payload.actor_id, payload.actor_role, payload.decision, payload.notes)
    if next_state == current_state:
        await record_audit(
            current_user.get("id", "unknown"),
            "workflow.decision",
            "run",
            run_id,
            decision=payload.decision,
            metadata={"state": current_state, "actor_id": payload.actor_id, "actor_role": payload.actor_role},
        )
        return {"run_id": run_id, "workflow_state": current_state, "message": entry.get("message")}

    await record_run_event(
        run_id,
        "workflow.approval_decision",
        {"from": current_state, "to": next_state, "decision": payload.decision},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.decision",
        "run",
        run_id,
        decision=payload.decision,
        metadata={"from": current_state, "to": next_state, "reason": payload.notes},
    )
    logger.info(
        "workflow.approval_decision",
        extra={"payload": {"run_id": run_id, "from": current_state, "to": next_state, "decision": payload.decision}},
    )
    await db.runs.update_one(
        {"id": run_id},
        {
            "$set": {
                "workflow_state": next_state,
                "workflow_status": "completed" if next_state in TERMINAL_WORKFLOW_STATES else "running",
                "pending_approval": None,
            },
            "$push": {"workflow_history": entry},
        },
    )

    return {
        "run_id": run_id,
        "workflow_state": next_state,
        "decision": payload.decision,
    }

@router.post("/workflow/{run_id}/auto-run")
async def auto_run_workflow(run_id: str, payload: WorkflowAutoRunRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Auto-run workflow transitions until approval or terminal state.

    Args:
        run_id: Run identifier.
        payload: Auto-run payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Auto-run result.

    Raises:
        HTTPException: If run is not found or state invalid.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    current_state = run.get("workflow_state", "incident_created")
    if current_state not in WORKFLOW_STATES:
        raise HTTPException(status_code=400, detail="Unknown workflow state")

    transitions = []
    steps = 0
    while current_state not in TERMINAL_WORKFLOW_STATES and current_state not in APPROVAL_STATES:
        if steps >= payload.max_steps:
            break
        next_state, new_entries = await advance_workflow(run, payload.actor_id, payload.outcome, payload.notes)
        if not new_entries:
            break
        await record_run_event(run_id, "workflow.state_changed", {"from": current_state, "to": next_state})
        await record_audit(
            current_user.get("id", "unknown"),
            "workflow.auto_run",
            "run",
            run_id,
            metadata={"from": current_state, "to": next_state, "reason": payload.notes},
        )
        logger.info(
            "workflow.state_changed",
            extra={"payload": {"run_id": run_id, "from": current_state, "to": next_state}},
        )
        transitions.extend(new_entries)
        current_state = next_state
        run["workflow_state"] = current_state
        steps += 1

    pending_approval = None
    workflow_status = "running"
    if current_state in APPROVAL_STATES:
        workflow_status = "awaiting_approval"
        pending_approval = await db.approvals.find_one(
            {"resource_type": "run", "resource_id": run_id, "action": current_state, "status": "pending"},
            {"_id": 0},
        )
    if current_state in TERMINAL_WORKFLOW_STATES:
        workflow_status = "completed"

    if transitions:
        await db.runs.update_one(
            {"id": run_id},
            {
                "$set": {
                    "workflow_state": current_state,
                    "workflow_status": workflow_status,
                    "pending_approval": pending_approval,
                },
                "$push": {"workflow_history": {"$each": transitions}},
            },
        )

    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.auto_run",
        "run",
        run_id,
        metadata={"steps": steps, "final_state": current_state, "actor_id": payload.actor_id},
    )

    return {
        "run_id": run_id,
        "workflow_state": current_state,
        "workflow_status": workflow_status,
        "approval_required": current_state in APPROVAL_STATES,
        "is_terminal": current_state in TERMINAL_WORKFLOW_STATES,
        "transitions": transitions,
    }


@router.post("/workflow/{run_id}/freeze")
async def freeze_workflow(run_id: str, payload: WorkflowAdvanceRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Freeze a workflow.

    Args:
        run_id: Run identifier.
        payload: Freeze payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Freeze result.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    entry = {
        "state": "frozen",
        "actor_id": payload.actor_id,
        "notes": payload.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.runs.update_one(
        {"id": run_id},
        {
            "$set": {"workflow_state": "frozen", "workflow_status": "frozen", "pending_approval": None},
            "$push": {"workflow_history": entry},
        },
    )
    await record_run_event(run_id, "workflow.frozen", {"actor": payload.actor_id, "notes": payload.notes})
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.frozen",
        "run",
        run_id,
        metadata={"actor": payload.actor_id, "notes": payload.notes, "reason": payload.notes},
    )
    logger.info(
        "workflow.frozen",
        extra={"payload": {"run_id": run_id, "actor": payload.actor_id}},
    )
    return {"run_id": run_id, "workflow_state": "frozen", "workflow_status": "frozen"}


@router.post("/workflow/{run_id}/rollback")
async def rollback_workflow(run_id: str, payload: WorkflowAdvanceRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Rollback a workflow.

    Args:
        run_id: Run identifier.
        payload: Rollback payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Rollback result.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    entry = {
        "state": "rolled_back",
        "actor_id": payload.actor_id,
        "notes": payload.notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.runs.update_one(
        {"id": run_id},
        {
            "$set": {"workflow_state": "rolled_back", "workflow_status": "completed", "pending_approval": None},
            "$push": {"workflow_history": entry},
        },
    )
    await record_run_event(run_id, "workflow.rolled_back", {"actor": payload.actor_id, "notes": payload.notes})
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.rolled_back",
        "run",
        run_id,
        metadata={"actor": payload.actor_id, "notes": payload.notes, "reason": payload.notes},
    )
    logger.info(
        "workflow.rolled_back",
        extra={"payload": {"run_id": run_id, "actor": payload.actor_id}},
    )
    return {"run_id": run_id, "workflow_state": "rolled_back", "workflow_status": "completed"}


@router.post("/workflow/{run_id}/reset")
async def reset_workflow(run_id: str, payload: WorkflowAdvanceRequest, current_user: dict = Depends(require_permission("workflow:control"))) -> Dict[str, Any]:
    """Reset a workflow to initial state.

    Args:
        run_id: Run identifier.
        payload: Reset payload.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Reset result.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    await db.runs.update_one(
        {"id": run_id},
        {
            "$set": {
                "workflow_state": "incident_created",
                "workflow_status": "running",
                "pending_approval": None,
                "workflow_history": [],
            }
        },
    )
    await record_run_event(run_id, "workflow.reset", {"actor": payload.actor_id, "notes": payload.notes})
    await record_audit(
        current_user.get("id", "unknown"),
        "workflow.reset",
        "run",
        run_id,
        metadata={"actor": payload.actor_id, "notes": payload.notes, "reason": payload.notes},
    )
    logger.info(
        "workflow.reset",
        extra={"payload": {"run_id": run_id, "actor": payload.actor_id}},
    )
    return {"run_id": run_id, "workflow_state": "incident_created", "workflow_status": "running"}
