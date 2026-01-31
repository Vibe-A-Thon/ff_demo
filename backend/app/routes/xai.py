from fastapi import APIRouter, HTTPException
from app.db import db
from app.xai_utils import build_evidence_items, build_explanation_bundle
from app.run_helpers import record_run_event

router = APIRouter()

@router.get("/xai/explain/{run_id}")
async def explain_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = run.get("last_decision", "monitor")
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)
    bundle = build_explanation_bundle(run_id, decision, evidence_items)

    await record_run_event(run_id, "xai.generated", {
        "decision": decision,
        "bundle_id": bundle.bundle_id,
        "evidence_count": len(evidence_items),
    })

    return bundle
