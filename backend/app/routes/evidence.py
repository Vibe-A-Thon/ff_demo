from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import EvidencePack, EvidenceExportApprovalRequest, ApprovalRequest
from app.xai_utils import build_evidence_items, build_explanation_bundle
from app.audit import record_audit, redact_evidence_pack, compute_checksum

router = APIRouter()


def _normalize_approval_chain(approvals):
    chain = []
    for approval in approvals or []:
        approvers = approval.get("approvers") or []
        if approvers:
            for approver in approvers:
                chain.append(
                    {
                        "stage": approval.get("action"),
                        "status": approval.get("status"),
                        "approver_id": approver.get("approver_id"),
                        "timestamp": approver.get("timestamp"),
                        "notes": approver.get("notes"),
                        "approval_action": approver.get("approval_action"),
                    }
                )
        else:
            chain.append(
                {
                    "stage": approval.get("action"),
                    "status": approval.get("status"),
                    "approver_id": approval.get("requestor_id"),
                    "timestamp": approval.get("created_at"),
                }
            )
    return chain


async def _fetch_approvals(run_id: str | None, pack_id: str | None):
    approvals = []
    if run_id:
        approvals.extend(
            await db.approvals.find(
                {"resource_type": "run", "resource_id": run_id},
                {"_id": 0},
            ).to_list(200)
        )
    if pack_id:
        approvals.extend(
            await db.approvals.find(
                {"resource_type": "evidence_pack", "resource_id": pack_id},
                {"_id": 0},
            ).to_list(50)
        )
    return _normalize_approval_chain(approvals)


def _extract_triggered_rules(events):
    rules = set()
    for event in events:
        payload = event.get("payload", {})
        outputs = payload.get("outputs") or {}
        for candidate in [payload.get("rule_id"), outputs.get("rule_id")]:
            if candidate:
                rules.add(candidate)
        rulespec = outputs.get("rulespec") or payload.get("rulespec")
        if isinstance(rulespec, dict):
            rid = rulespec.get("rule_id")
            if rid:
                rules.add(rid)
        triggered_rules = outputs.get("triggered_rules") or payload.get("triggered_rules")
        if isinstance(triggered_rules, list):
            for rule_id in triggered_rules:
                if rule_id:
                    rules.add(rule_id)
    return list(rules)


def _build_artifacts_from_events(events):
    artifacts = []
    for event in events:
        if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
            continue
        payload = event.get("payload", {})
        artifacts.append(
            {
                "event_id": event.get("id"),
                "event_type": event.get("event_type"),
                "team": payload.get("team"),
                "agent": payload.get("agent"),
                "outputs": payload.get("outputs", {}),
                "created_at": event.get("created_at"),
            }
        )
    return artifacts


def _build_stage_summaries(events):
    summaries = []
    for event in events:
        if event.get("event_type") != "stage.changed":
            continue
        payload = event.get("payload", {})
        summaries.append(
            {
                "stage": payload.get("stage"),
                "step": payload.get("step"),
                "timestamp": event.get("created_at"),
            }
        )
    return summaries

@router.get("/evidence-packs")
async def get_evidence_packs():
    packs = await db.evidence_packs.find({}, {"_id": 0}).to_list(100)
    hydrated = []
    for pack in packs:
        approvals = await _fetch_approvals(pack.get("run_id"), pack.get("id"))
        pack["approvals"] = approvals
        hydrated.append(pack)
    return hydrated

@router.get("/evidence-packs/{pack_id}")
async def get_evidence_pack(pack_id: str):
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    pack["approvals"] = await _fetch_approvals(pack.get("run_id"), pack_id)
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

    events = [
        {
            "run_id": battle_id,
            "event_type": turn.get("event_type", "battle.turn"),
            "payload": turn,
        }
        for turn in battle.get("turns", [])
    ]
    decision = "review" if battle.get("turns") else "monitor"
    evidence_items = build_evidence_items(events)
    xai_bundle = build_explanation_bundle(battle_id, decision, evidence_items)
    pack_data["xai_bundle"] = xai_bundle.model_dump()

    pack = EvidencePack(**pack_data)
    pack_dict = pack.model_dump()
    pack_dict["checksum"] = compute_checksum(pack_dict)

    await db.evidence_packs.insert_one(pack_dict)
    return pack_dict


@router.post("/evidence-packs/generate/run/{run_id}")
async def generate_evidence_pack_from_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    triggered_rules = _extract_triggered_rules(events)
    stage_summaries = _build_stage_summaries(events)
    artifacts = _build_artifacts_from_events(events)

    narrative = (
        f"War loop run '{run_id}' completed stage '{run.get('current_stage')}'. "
        f"Workflow state: {run.get('workflow_state', 'incident_created')}."
    )

    decision = run.get("last_decision", "monitor")
    evidence_items = build_evidence_items(events)
    xai_bundle = build_explanation_bundle(run_id, decision, evidence_items)

    approvals = await _fetch_approvals(run_id, None)

    pack_data = {
        "run_id": run_id,
        "narrative": narrative,
        "triggered_rules": triggered_rules,
        "contributing_factors": [
            {"factor": "Run pipeline coverage", "weight": 0.86},
            {"factor": "Approval readiness", "weight": 0.74},
        ],
        "confidence": 0.9,
        "logs": events[-20:],
        "artifacts": artifacts,
        "workflow_history": run.get("workflow_history", []),
        "workflow_state": run.get("workflow_state"),
        "metrics": run.get("last_metrics", {}),
        "approvals": approvals,
        "xai_bundle": xai_bundle.model_dump(),
        "stage_summaries": stage_summaries,
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

    pack["approvals"] = await _fetch_approvals(pack.get("run_id"), pack_id)
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
