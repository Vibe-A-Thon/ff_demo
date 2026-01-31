from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import openai
from app.config import OPENAI_API_KEY
from app.db import db
from app.xai_utils import build_evidence_items, build_explanation_bundle
from app.run_helpers import record_run_event

router = APIRouter()

openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


class CommentorRequest(BaseModel):
    screen: str = Field(..., description="Current screen or route")
    role: str = Field("analyst", description="Active user role")
    summary: str | None = None
    highlights: list[str] = []
    timestamp: str | None = None


class CommentorResponse(BaseModel):
    text: str
    generated_by: str = "synthetic"
    timestamp: str

@router.get("/xai/explain/{run_id}")
async def explain_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = run.get("last_decision", "monitor")
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)
    bundle = build_explanation_bundle(run_id, decision, evidence_items)

    similar_cases = []
    packs = await db.evidence_packs.find({}, {"_id": 0}).sort("created_at", -1).to_list(3)
    for pack in packs:
        similar_cases.append(
            {
                "case_id": pack.get("id"),
                "summary": pack.get("narrative", "Evidence pack summary"),
                "similarity": 0.82,
                "metadata": {"battle_id": pack.get("battle_id")},
            }
        )
    bundle.similar_cases = similar_cases

    await record_run_event(run_id, "xai.generated", {
        "decision": decision,
        "bundle_id": bundle.bundle_id,
        "evidence_count": len(evidence_items),
        "similar_cases": len(similar_cases),
    })

    return bundle


@router.get("/xai/explain/{run_id}/full")
async def explain_run_full(run_id: str):
    bundle = await explain_run(run_id)
    return {
        "bundle": bundle,
        "evidence_graph": bundle.evidence_graph,
        "counterfactuals": bundle.counterfactuals,
        "similar_cases": bundle.similar_cases,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/xai/package/{package_id}")
async def explain_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB package not found")

    if package.get("xai_bundle"):
        return {"bundle": package.get("xai_bundle"), "source": "package"}

    run_id = package.get("run_id") or (package.get("manifest", {}) or {}).get("run_id")
    if run_id:
        bundle = await explain_run(run_id)
        return {"bundle": bundle, "source": "run"}

    return {"bundle": None, "source": "none"}


@router.post("/xai/commentary", response_model=CommentorResponse)
async def generate_commentary(payload: CommentorRequest):
    now = datetime.now(timezone.utc).isoformat()
    highlights = ", ".join(payload.highlights[:6]) if payload.highlights else "key activity updates"
    prompt = (
        "You are The Commentor, an explainability agent. "
        "Describe what is happening on the current screen in 2-3 concise sentences, present tense. "
        "Do not invent sensitive identifiers or personal data. "
        f"Screen: {payload.screen}. Role: {payload.role}. "
        f"Summary: {payload.summary or 'Operational overview.'}. "
        f"Highlights: {highlights}."
    )

    if openai_client:
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You provide safe, concise UI commentary."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
            )
            text = response.choices[0].message.content.strip()
            return CommentorResponse(text=text, generated_by="openai", timestamp=now)
        except Exception:
            pass

    fallback = (
        f"On {payload.screen}, the {payload.role} view highlights {highlights}. "
        "Controls and telemetry are updating in real time as operations progress."
    )
    return CommentorResponse(text=fallback, generated_by="synthetic", timestamp=now)
