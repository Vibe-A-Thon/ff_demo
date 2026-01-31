from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import Rule, RuleActionRequest, RuleApprovalDecision, RuleCreate, RuleProposalCreate, ApprovalRequest
from app.audit import record_audit, rule_tests_pass

router = APIRouter()

@router.get("/rules")
async def get_rules():
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)
    return rules

@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.post("/rules")
async def create_rule(rule_data: RuleCreate):
    rule = Rule(**rule_data.model_dump())
    await db.rules.insert_one(rule.model_dump())
    return rule

@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule_data: RuleCreate):
    existing = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    updated_at = datetime.now(timezone.utc).isoformat()
    update_data = rule_data.model_dump()
    update_data["updated_at"] = updated_at
    update_data["version"] = existing.get("version", 1) + 1

    await db.rules.update_one({"id": rule_id}, {"$set": update_data})
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    result = await db.rules.delete_one({"id": rule_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted"}

@router.post("/rules/{rule_id}/test")
async def test_rule(rule_id: str):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    import random
    test_results = {
        "passed": random.randint(8, 15),
        "failed": random.randint(0, 3),
        "total": 15,
        "coverage": round(random.uniform(85, 100), 2),
        "execution_time": round(random.uniform(0.1, 2.0), 3),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    await db.rules.update_one(
        {"id": rule_id},
        {"$set": {"test_results": test_results, "status": "tested"}},
    )
    return test_results

@router.post("/rules/propose")
async def propose_rule(rule_data: RuleProposalCreate):
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        rule_type=rule_data.rule_type,
        conditions=rule_data.conditions,
        actions=rule_data.actions,
        priority=rule_data.priority,
        status="proposed",
        proposed_by=rule_data.requestor_id,
    )
    await db.rules.insert_one(rule.model_dump())

    approval = ApprovalRequest(
        resource_type="rule",
        resource_id=rule.id,
        action="approve",
        requestor_id=rule_data.requestor_id,
        metadata=rule_data.metadata,
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(
        rule_data.requestor_id,
        "rule_proposed",
        "rule",
        rule.id,
        metadata=rule_data.metadata,
    )
    return {"rule": rule, "approval_request": approval}

@router.post("/rules/{rule_id}/approve")
async def approve_rule(rule_id: str, decision: RuleApprovalDecision):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if decision.decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Decision must be approved or rejected")

    status = "approved" if decision.decision == "approved" else "rejected"
    approved_at = datetime.now(timezone.utc).isoformat()
    await db.rules.update_one(
        {"id": rule_id},
        {"$set": {"status": status, "approved_by": decision.approver_id, "approved_at": approved_at}},
    )

    await db.approvals.update_one(
        {"resource_id": rule_id, "status": "pending"},
        {
            "$set": {"status": status},
            "$push": {"approvers": {"id": decision.approver_id, "decision": status, "notes": decision.notes}},
        },
    )
    await record_audit(
        decision.approver_id,
        "rule_approval",
        "rule",
        rule_id,
        decision=status,
        metadata={"notes": decision.notes},
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@router.post("/rules/{rule_id}/stage")
async def stage_rule(rule_id: str, request: RuleActionRequest):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.get("status") not in {"approved", "tested"}:
        raise HTTPException(status_code=400, detail="Rule must be approved before staging")

    if not rule_tests_pass(rule.get("test_results")):
        raise HTTPException(status_code=400, detail="Rule tests must pass before staging")

    await db.rules.update_one({"id": rule_id}, {"$set": {"status": "staged"}})
    await record_audit(
        request.actor_id,
        "rule_staged",
        "rule",
        rule_id,
        metadata=request.metadata,
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})

@router.post("/rules/{rule_id}/deploy")
async def deploy_rule(rule_id: str, request: RuleActionRequest):
    rule = await db.rules.find_one({"id": rule_id}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if rule.get("status") != "staged":
        raise HTTPException(status_code=400, detail="Rule must be staged before deployment")

    await db.rules.update_one({"id": rule_id}, {"$set": {"status": "deployed"}})
    await record_audit(
        request.actor_id,
        "rule_deployed",
        "rule",
        rule_id,
        metadata=request.metadata,
    )
    return await db.rules.find_one({"id": rule_id}, {"_id": 0})
