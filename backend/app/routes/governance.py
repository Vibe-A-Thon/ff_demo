"""Governance routes for approvals and audit."""

from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.models import ApprovalRequest
from app.audit import record_audit
from app.core.logging_config import get_logger
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

REQUIRED_APPROVAL_STAGES = ["orange_review_approve", "white_compliance_audit"]

@router.post("/runs/{run_id}/request-approval")
async def request_run_approval(
    run_id: str,
    stage: str,
    requestor_id: str,
    current_user: dict = Depends(require_permission("approvals:write")),
):
    """Request approval for a run stage.

    Args:
        run_id: Run identifier.
        stage: Approval stage.
        requestor_id: Requestor identifier.

    Returns:
        ApprovalRequest: Created approval.

    Raises:
        HTTPException: If the stage does not require approval.
    """
    if stage not in REQUIRED_APPROVAL_STAGES:
        raise HTTPException(status_code=400, detail="Stage does not require approval")

    approval = ApprovalRequest(
        resource_type="run",
        resource_id=run_id,
        action=stage,
        requestor_id=requestor_id,
        metadata={"stage": stage},
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(requestor_id, "approval.requested", "run", run_id, metadata={"stage": stage, "approval_id": approval.id})
    logger.info(
        "governance.approval.requested",
        extra={"payload": {"run_id": run_id, "stage": stage, "approval_id": approval.id}},
    )
    return approval

@router.get("/runs/{run_id}/safe-to-proceed")
async def safe_to_proceed(run_id: str, current_user: dict = Depends(require_permission("workflow:read"))):
    """Check whether a run is safe to proceed.

    Args:
        run_id: Run identifier.

    Returns:
        dict: Safety status and missing approvals.

    Raises:
        None: No explicit exceptions are raised.
    """
    approvals = await db.approvals.find({"resource_id": run_id, "resource_type": "run"}, {"_id": 0}).to_list(50)
    approved_actions = {a.get("action") for a in approvals if a.get("status") == "approved"}
    missing = [stage for stage in REQUIRED_APPROVAL_STAGES if stage not in approved_actions]
    logger.info(
        "governance.safe_to_proceed",
        extra={"payload": {"run_id": run_id, "safe": len(missing) == 0, "missing": missing}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "governance.safe_to_proceed",
        "run",
        run_id,
        metadata={"safe": len(missing) == 0, "missing": missing},
    )
    return {"run_id": run_id, "safe_to_proceed": len(missing) == 0, "missing": missing}

@router.get("/audit/logs")
async def get_audit_logs(current_user: dict = Depends(require_permission("audit:read"))):
    """List audit log entries.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        list[dict]: Audit log entries.

    Raises:
        None: No explicit exceptions are raised.
    """
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    await record_audit(
        current_user.get("id", "unknown"),
        "audit.logs.read",
        "audit_log",
        "list",
    )
    return logs
