from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import EvidencePack, EvidenceExportApprovalRequest, ApprovalRequest
from app.audit import record_audit, redact_evidence_pack, compute_checksum

router = APIRouter()

@router.get("/evidence-packs")
async def get_evidence_packs():
    packs = await db.evidence_packs.find({}, {"_id": 0}).to_list(100)
    return packs

@router.get("/evidence-packs/{pack_id}")
async def get_evidence_pack(pack_id: str):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    return pack

@router.post("/evidence-packs/generate/{battle_id}")
async def generate_evidence_pack(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    pack_data = {
        "battle_id": battle_id,
        "narrative": f"Battle '{battle['scenario_name']}' completed with {len(battle.get('turns', []))} turns.",
        "triggered_rules": [t.get("rule_id", "unknown") for t in battle.get("turns", []) if t.get("rule_id")],
        "contributing_factors": [
            {"factor": "Pattern match", "weight": 0.8},
            {"factor": "Velocity check", "weight": 0.6},
        ],
        "confidence": 0.92,
        "logs": battle.get("turns", [])[-10:] if battle.get("turns") else [],
    }

    pack = EvidencePack(**pack_data)
    pack_dict = pack.model_dump()
    pack_dict["checksum"] = compute_checksum(pack_dict)

    await db.evidence_packs.insert_one(pack_dict)
    return pack_dict

@router.get("/evidence-packs/{pack_id}/export")
async def export_evidence_pack(pack_id: str, mode: str = "internal", requestor_id: str | None = None):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    if mode not in {"internal", "external"}:
        raise HTTPException(status_code=400, detail="Invalid export mode")

    if mode == "external":
        approval = await db.approvals.find_one(
            {
                "resource_type": "evidence_pack",
                "resource_id": pack_id,
                "action": "export",
                "status": "approved",
            },
            {"_id": 0},
        )
        if not approval:
            raise HTTPException(status_code=403, detail="External export requires approval")

    redacted_pack = redact_evidence_pack(pack, mode)
    if requestor_id:
        await record_audit(
            requestor_id,
            "evidence_pack_export",
            "evidence_pack",
            pack_id,
            decision=mode,
            metadata={"mode": mode},
        )

    return {
        "filename": f"evidence_pack_{pack_id}.json",
        "content_type": "application/json",
        "data": redacted_pack,
        "checksum": pack.get("checksum", ""),
        "export_mode": mode,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

@router.post("/evidence-packs/{pack_id}/request-export-approval")
async def request_evidence_export_approval(pack_id: str, request: EvidenceExportApprovalRequest):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    approval = ApprovalRequest(
        resource_type="evidence_pack",
        resource_id=pack_id,
        action="export",
        requestor_id=request.requestor_id,
        metadata={"mode": request.mode, **request.metadata},
    )
    await db.approvals.insert_one(approval.model_dump())
    await record_audit(
        request.requestor_id,
        "evidence_pack_export_requested",
        "evidence_pack",
        pack_id,
        metadata=approval.metadata,
    )
    return approval
