"""Evidence pack routes.

Generate and retrieve evidence packs for battles and runs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO
from app.db import db
from app.core.logging_config import get_logger
from app.models import EvidencePack, EvidenceExportApprovalRequest, ApprovalRequest
from app.xai_utils import build_evidence_items, build_explanation_bundle
from app.audit import record_audit, redact_evidence_pack, compute_checksum, build_checksum_chain_entry
from app.pdf_utils import build_evidence_pack_pdf, build_story_report_pdf
from app.story_report import build_story_report, build_story_markdown
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)


def _normalize_approval_chain(approvals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize approval chain entries.

    Args:
        approvals: Raw approval documents.

    Returns:
        List[Dict[str, Any]]: Normalized approval chain.

    Raises:
        None: No explicit exceptions are raised.
    """
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


async def _fetch_approvals(run_id: str | None, pack_id: str | None) -> List[Dict[str, Any]]:
    """Fetch approvals for run and/or evidence pack.

    Args:
        run_id: Optional run identifier.
        pack_id: Optional evidence pack identifier.

    Returns:
        List[Dict[str, Any]]: Normalized approvals.

    Raises:
        None: No explicit exceptions are raised.
    """
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


def _extract_triggered_rules(events: List[Dict[str, Any]]) -> List[str]:
    """Extract triggered rule IDs from events.

    Args:
        events: Event payloads.

    Returns:
        List[str]: Unique rule identifiers.

    Raises:
        None: No explicit exceptions are raised.
    """
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


def _build_artifacts_from_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build artifact summaries from events.

    Args:
        events: Event payloads.

    Returns:
        List[Dict[str, Any]]: Artifact summaries.

    Raises:
        None: No explicit exceptions are raised.
    """
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


def _build_stage_summaries(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize workflow stage events.

    Args:
        events: Event payloads.

    Returns:
        List[Dict[str, Any]]: Stage summaries.

    Raises:
        None: No explicit exceptions are raised.
    """
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
async def get_evidence_packs(current_user: dict = Depends(require_permission("evidence:read"))) -> List[Dict[str, Any]]:
    """List evidence packs.

    Args:
        current_user: Authorized user context.

    Returns:
        List[Dict[str, Any]]: Evidence packs.

    Raises:
        None: No explicit exceptions are raised.
    """
    packs = await db.evidence_packs.find({}, {"_id": 0}).to_list(100)
    hydrated = []
    for pack in packs:
        approvals = await _fetch_approvals(pack.get("run_id"), pack.get("id"))
        pack["approvals"] = approvals
        hydrated.append(pack)
    await record_audit(
        current_user.get("id", "unknown"),
        "evidence_pack.list",
        "evidence_pack",
        "list",
    )
    return hydrated

@router.get("/evidence-packs/{pack_id}")
async def get_evidence_pack(pack_id: str, current_user: dict = Depends(require_permission("evidence:read"))) -> Dict[str, Any]:
    """Get an evidence pack by ID.

    Args:
        pack_id: Evidence pack identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Evidence pack.

    Raises:
        HTTPException: If pack is not found.
    """
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    pack["approvals"] = await _fetch_approvals(pack.get("run_id"), pack_id)
    await record_audit(
        current_user.get("id", "unknown"),
        "evidence_pack.read",
        "evidence_pack",
        pack_id,
    )
    return pack

@router.post("/evidence-packs/generate/{battle_id}")
async def generate_evidence_pack(battle_id: str, current_user: dict = Depends(require_permission("evidence:write"))) -> Dict[str, Any]:
    """Generate an evidence pack from a battle.

    Args:
        battle_id: Battle identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Evidence pack payload.

    Raises:
        HTTPException: If battle is not found.
    """
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
    xai_bundle = build_explanation_bundle(battle_id, decision, evidence_items, None)
    pack_data["xai_bundle"] = xai_bundle.model_dump()

    approvals = await _fetch_approvals(None, None)
    story_report = build_story_report(pack_data, None, events, approvals)
    story_markdown = build_story_markdown(story_report)

    pack = EvidencePack(**pack_data)
    pack_dict = pack.model_dump()
    pack_dict["checksum"] = compute_checksum(pack_dict)
    pack_dict["story_report"] = story_report
    pack_dict["story_markdown"] = story_markdown
    pack_dict["checksum_chain"] = [
        build_checksum_chain_entry(
            {**pack_dict, "checksum_chain": []},
            previous_hash=None,
            signer_id="system",
            context={"action": "pack.generated", "source": "battle"},
        )
    ]

    await db.evidence_packs.insert_one(pack_dict)
    await record_audit(
        current_user.get("id", "unknown"),
        "evidence.pack.generated",
        "evidence_pack",
        pack_dict.get("id"),
        metadata={"battle_id": battle_id, "source": "battle"},
    )
    logger.info(
        "evidence.pack.generated",
        extra={"payload": {"pack_id": pack_dict.get("id"), "battle_id": battle_id, "source": "battle"}},
    )
    return pack_dict


@router.post("/evidence-packs/generate/run/{run_id}")
async def generate_evidence_pack_from_run(run_id: str, current_user: dict = Depends(require_permission("evidence:write"))) -> Dict[str, Any]:
    """Generate an evidence pack from a run.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, Any]: Evidence pack payload.

    Raises:
        HTTPException: If run is not found.
    """
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
    xai_bundle = build_explanation_bundle(run_id, decision, evidence_items, run.get("last_metrics", {}))

    approvals = await _fetch_approvals(run_id, None)
    llm_events = await db.audit_logs.find(
        {"target_type": "llm", "metadata.run_id": run_id},
        {"_id": 0},
    ).sort("created_at", 1).to_list(200)
    model_pins = {}
    for entry in llm_events:
        meta = entry.get("metadata", {})
        model_id = entry.get("target_id")
        if not model_id:
            continue
        model_pins[model_id] = {
            "model_id": model_id,
            "provider": meta.get("provider"),
            "model_name": meta.get("model_name"),
            "version_pin": meta.get("version_pin"),
        }

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
        "llm_events": llm_events,
        "llm_model_pins": list(model_pins.values()),
    }

    story_report = build_story_report(pack_data, run, events, approvals)
    story_markdown = build_story_markdown(story_report)

    pack = EvidencePack(**pack_data)
    pack_dict = pack.model_dump()
    pack_dict["checksum"] = compute_checksum(pack_dict)
    pack_dict["story_report"] = story_report
    pack_dict["story_markdown"] = story_markdown
    pack_dict["checksum_chain"] = [
        build_checksum_chain_entry(
            {**pack_dict, "checksum_chain": []},
            previous_hash=None,
            signer_id="system",
            context={"action": "pack.generated", "source": "run"},
        )
    ]

    await db.evidence_packs.insert_one(pack_dict)
    await record_audit(
        current_user.get("id", "unknown"),
        "evidence.pack.generated",
        "evidence_pack",
        pack_dict.get("id"),
        metadata={"run_id": run_id, "source": "run"},
    )
    logger.info(
        "evidence.pack.generated",
        extra={"payload": {"pack_id": pack_dict.get("id"), "run_id": run_id, "source": "run"}},
    )
    return pack_dict

@router.get("/evidence-packs/{pack_id}/export")
async def export_evidence_pack(
    pack_id: str,
    mode: str = "internal",
    format: str = "json",
    requestor_id: str | None = None,
    current_user: dict = Depends(require_permission("evidence:read")),
) -> Dict[str, Any]:
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    if mode not in {"internal", "external"}:
        raise HTTPException(status_code=400, detail="Invalid export mode")

    if format not in {"json", "pdf", "story", "story_pdf"}:
        raise HTTPException(status_code=400, detail="Invalid export format")

    if mode == "external":
        if requestor_id and requestor_id == current_user.get("id"):
            raise HTTPException(status_code=403, detail="SoD violation: requester cannot export own evidence")
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
    chain = pack.get("checksum_chain", [])
    previous_hash = chain[-1]["payload_hash"] if chain else None
    export_context = {
        "action": "pack.exported",
        "mode": mode,
        "format": format,
        "requestor_id": requestor_id,
    }
    export_entry = build_checksum_chain_entry(
        {
            "pack_id": pack_id,
            "checksum": pack.get("checksum", ""),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "format": format,
        },
        previous_hash=previous_hash,
        signer_id=current_user.get("id", "system"),
        context=export_context,
    )
    chain.append(export_entry)
    await db.evidence_packs.update_one({"id": pack_id}, {"$set": {"checksum_chain": chain}})
    redacted_pack["checksum_chain"] = chain
    await record_audit(
        current_user.get("id", "unknown"),
        "evidence_pack.exported",
        "evidence_pack",
        pack_id,
        decision=mode,
        metadata={
            "mode": mode,
            "requestor_id": requestor_id,
            "evidence_links": [f"evidence_pack:{pack_id}"],
        }
        if requestor_id
        else {"mode": mode, "evidence_links": [f"evidence_pack:{pack_id}"]},
    )
    if requestor_id:
        await record_audit(
            requestor_id,
            "evidence_pack_export",
            "evidence_pack",
            pack_id,
            decision=mode,
            metadata={"mode": mode, "evidence_links": [f"evidence_pack:{pack_id}"]},
        )

    if format == "pdf":
        pdf_bytes = build_evidence_pack_pdf(redacted_pack)
        filename = f"evidence_pack_{pack_id}.pdf"
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format in {"story", "story_pdf"}:
        run = None
        events = []
        if pack.get("run_id"):
            run = await db.runs.find_one({"id": pack.get("run_id")}, {"_id": 0})
            events = await db.run_events.find({"run_id": pack.get("run_id")}, {"_id": 0}).sort("created_at", 1).to_list(1000)
        else:
            events = pack.get("logs", [])
        approvals = await _fetch_approvals(pack.get("run_id"), pack_id)
        report = build_story_report(redacted_pack, run, events, approvals)
        markdown = build_story_markdown(report)
        if format == "story_pdf":
            pdf_bytes = build_story_report_pdf(report)
            filename = f"evidence_story_{pack_id}.pdf"
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        return {
            "filename": f"evidence_story_{pack_id}.md",
            "content_type": "text/markdown",
            "data": markdown,
            "report": report,
            "checksum": pack.get("checksum", ""),
            "export_mode": mode,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "filename": f"evidence_pack_{pack_id}.json",
        "content_type": "application/json",
        "data": redacted_pack,
        "checksum": pack.get("checksum", ""),
        "export_mode": mode,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

@router.post("/evidence-packs/{pack_id}/request-export-approval")
async def request_evidence_export_approval(
    pack_id: str,
    request: EvidenceExportApprovalRequest,
    current_user: dict = Depends(require_permission("evidence:write")),
):
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
        metadata={
            **approval.metadata,
            "mode": request.mode,
            "reason": (request.metadata or {}).get("reason"),
            "evidence_links": [f"evidence_pack:{pack_id}"],
        },
    )
    return approval
