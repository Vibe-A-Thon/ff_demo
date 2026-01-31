from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import ApprovalCreate, ApprovalRequest
from app.audit import record_audit

router = APIRouter()

@router.get("/approvals")
async def get_approvals():
    approvals = await db.approvals.find({}, {"_id": 0}).to_list(100)
    return approvals

@router.post("/approvals")
async def create_approval(approval_data: ApprovalCreate):
    approval = ApprovalRequest(**approval_data.model_dump())
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(approval.requestor_id, "approval.requested", "approval", approval.id, metadata=approval.metadata)
    return approval

@router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: str, approver_id: str):
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
    return {"message": "Approved"}

@router.post("/approvals/{approval_id}/reject")
async def reject_request(approval_id: str, approver_id: str):
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
    return {"message": "Rejected"}
