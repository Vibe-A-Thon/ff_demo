"""Explainability (XAI) routes."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission
from app.deps import get_db, get_llm_client
from app.xai_utils import build_evidence_items, build_explanation_bundle
from app.run_helpers import record_run_event

router = APIRouter()
logger = get_logger(__name__)


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
async def explain_run(
    run_id: str,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
):
    """Generate an explanation bundle for a run.

    Args:
        run_id: Run identifier.
        db: Database client.

    Returns:
        Any: Explanation bundle.

    Raises:
        HTTPException: If run is not found.
    """
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

    await record_run_event(
        run_id,
        "xai.generated",
        {
            "decision": decision,
            "bundle_id": bundle.bundle_id,
            "evidence_count": len(evidence_items),
            "similar_cases": len(similar_cases),
        },
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "xai.bundle.generated",
        "run",
        run_id,
        metadata={"bundle_id": bundle.bundle_id, "evidence_links": [f"xai_bundle:{bundle.bundle_id}"]},
    )
    logger.info(
        "xai.bundle.generated",
        extra={"payload": {"run_id": run_id, "evidence": len(evidence_items), "similar_cases": len(similar_cases)}},
    )

    return bundle


@router.get("/xai/explain/{run_id}/full")
async def explain_run_full(
    run_id: str,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
):
    """Return explanation bundle with extended details.

    Args:
        run_id: Run identifier.
        db: Database client.

    Returns:
        dict: Full explanation payload.

    Raises:
        HTTPException: If run is not found.
    """
    bundle = await explain_run(run_id, current_user=current_user, db=db)
    return {
        "bundle": bundle,
        "evidence_graph": bundle.evidence_graph,
        "counterfactuals": bundle.counterfactuals,
        "similar_cases": bundle.similar_cases,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/xai/package/{package_id}")
async def explain_package(
    package_id: str,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
):
    """Get or derive XAI bundle for a package.

    Args:
        package_id: Package identifier.
        db: Database client.

    Returns:
        dict: Bundle payload.

    Raises:
        HTTPException: If package is not found.
    """
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB package not found")

    if package.get("xai_bundle"):
        await record_audit(
            current_user.get("id", "unknown"),
            "xai.package.bundle.read",
            "rsb_package",
            package_id,
            metadata={"source": "package"},
        )
        return {"bundle": package.get("xai_bundle"), "source": "package"}

    run_id = package.get("run_id") or (package.get("manifest", {}) or {}).get("run_id")
    if run_id:
        bundle = await explain_run(run_id, current_user=current_user, db=db)
        await record_audit(
            current_user.get("id", "unknown"),
            "xai.package.bundle.read",
            "rsb_package",
            package_id,
            metadata={"source": "run", "run_id": run_id},
        )
        return {"bundle": bundle, "source": "run"}

    await record_audit(
        current_user.get("id", "unknown"),
        "xai.package.bundle.read",
        "rsb_package",
        package_id,
        metadata={"source": "none"},
    )
    return {"bundle": None, "source": "none"}


@router.post("/xai/commentary", response_model=CommentorResponse)
async def generate_commentary(
    payload: CommentorRequest,
    current_user: dict = Depends(require_permission("xai:write")),
    llm_client: LLMClient | None = Depends(get_llm_client),
):
    """Generate UI commentary text.

    Args:
        payload: Commentary payload.
        llm_client: Optional LLM client.

    Returns:
        CommentorResponse: Generated commentary.

    Raises:
        None: No explicit exceptions are raised.
    """
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

    if llm_client:
        try:
            text = await llm_client.chat_completions_create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You provide safe, concise UI commentary."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
            )
            text = text.strip()
            logger.info(
                "xai.commentary.generated",
                extra={"payload": {"screen": payload.screen, "generated_by": "openai"}},
            )
            await record_audit(
                current_user.get("id", "unknown"),
                "xai.commentary.generated",
                "xai_commentary",
                payload.screen,
                metadata={"mode": "llm", "role": payload.role},
            )
            return CommentorResponse(text=text, generated_by="openai", timestamp=now)
        except Exception:
            pass

    fallback = (
        f"On {payload.screen}, the {payload.role} view highlights {highlights}. "
        "Controls and telemetry are updating in real time as operations progress."
    )
    logger.info(
        "xai.commentary.generated",
        extra={"payload": {"screen": payload.screen, "generated_by": "synthetic"}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "xai.commentary.generated",
        "xai_commentary",
        payload.screen,
        metadata={"mode": "synthetic", "role": payload.role},
    )
    return CommentorResponse(text=fallback, generated_by="synthetic", timestamp=now)
