"""Approval workflow routes.

Supports request creation and approval decisions.
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.core.logging_config import get_logger
from app.models import ApprovalCreate, ApprovalRequest
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/approvals")
async def get_approvals(current_user: dict = Depends(require_permission("approvals:read"))) -> List[Dict]:
    """List approval requests.

    Args:
        current_user: Authorized user context.

    Returns:
        List[Dict]: Approval requests.

    Raises:
        None: No explicit exceptions are raised.
    """
    approvals = await db.approvals.find({}, {"_id": 0}).to_list(100)
    return approvals

@router.post("/approvals")
async def create_approval(approval_data: ApprovalCreate, current_user: dict = Depends(require_permission("approvals:write"))) -> ApprovalRequest:
    """Create an approval request.

    Args:
        approval_data: Approval payload.
        current_user: Authorized user context.

    Returns:
        ApprovalRequest: Created approval request.

    Raises:
        None: No explicit exceptions are raised.
    """
    approval = ApprovalRequest(**approval_data.model_dump())
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(approval.requestor_id, "approval.requested", "approval", approval.id, metadata=approval.metadata)
    logger.info(
        "approval.requested",
        extra={"payload": {"approval_id": approval.id, "resource": approval.resource_type, "action": approval.action}},
    )
    return approval

@router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, approver_id: str, current_user: dict = Depends(require_permission("approvals:decide"))) -> Dict[str, str]:
    """Approve an approval request.

    Args:
        approval_id: Approval identifier.
        approver_id: Approver identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, str]: Result message.

    Raises:
        HTTPException: If the approval is not found.
    """
    approval = await db.approvals.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approver_entry = {
        "approver_id": approver_id,
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "action": "approved",
    }
    await db.approvals.update_one(
        {"id": approval_id},
        {"$push": {"approvers": approver_entry}, "$set": {"status": "approved"}},
    )
    await record_audit(approver_id, "approval.decision", "approval", approval_id, decision="approved")
    logger.info(
        "approval.decision",
        extra={"payload": {"approval_id": approval_id, "decision": "approved", "approver": approver_id}},
    )
    return {"message": "Approved"}

@router.post("/approvals/{approval_id}/reject")
async def reject_request(approval_id: str, approver_id: str, current_user: dict = Depends(require_permission("approvals:decide"))) -> Dict[str, str]:
    """Reject an approval request.

    Args:
        approval_id: Approval identifier.
        approver_id: Approver identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, str]: Result message.

    Raises:
        HTTPException: If the approval is not found.
    """
    approval = await db.approvals.find_one({"id": approval_id}, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approver_entry = {
        "approver_id": approver_id,
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "action": "rejected",
    }
    await db.approvals.update_one(
        {"id": approval_id},
        {"$push": {"approvers": approver_entry}, "$set": {"status": "rejected"}},
    )
    await record_audit(approver_id, "approval.decision", "approval", approval_id, decision="rejected")
    logger.info(
        "approval.decision",
        extra={"payload": {"approval_id": approval_id, "decision": "rejected", "approver": approver_id}},
    )
    return {"message": "Rejected"}
