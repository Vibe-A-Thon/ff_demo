"""Explainability (XAI) routes."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission
from app.deps import get_db, get_llm_client
from app.config import get_integration_setting
from app.xai_utils import (
    build_evidence_items,
    build_explanation_bundle,
    build_case_signature,
    build_pack_signature,
    score_case_similarity,
)
from app.services.counterfactual_service import (
    CounterfactualService,
    SimilarCaseService,
    build_enhanced_explanation_bundle,
)
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
    llm_client: LLMClient | None = Depends(get_llm_client),
):
    """Generate an enhanced explanation bundle for a run.

    This endpoint generates counterfactuals and similar-case matches linked to
    real evidence packs and telemetry data.

    Args:
        run_id: Run identifier.
        db: Database client.
        llm_client: Optional LLM client for enhanced explanations.

    Returns:
        ExplanationBundle: Complete explanation bundle with counterfactuals and similar cases.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = run.get("last_decision", "monitor")
    run_metrics = run.get("last_metrics", {})
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)
    
    # Initialize enhanced services
    cf_service = CounterfactualService(db_client=db, llm_client=llm_client)
    sc_service = SimilarCaseService(db_client=db)
    
    # Extract features and rules from evidence
    features = cf_service.extract_features_from_evidence(evidence_items)
    rules = cf_service.extract_rules_from_evidence(evidence_items, events)
    
    # Generate enhanced counterfactuals
    counterfactuals = cf_service.generate_combined_counterfactuals(
        features, rules, decision, run_metrics
    )
    
    # Build base explanation bundle
    bundle = build_explanation_bundle(run_id, decision, evidence_items, run_metrics)
    
    # Replace counterfactuals with enhanced version
    bundle.counterfactuals = counterfactuals
    
    # LLM-enhanced summary if available
    if llm_client:
        try:
            model_name = get_integration_setting("llm", "model", "gpt-4o") or "gpt-4o"
            
            # Build context for LLM
            cf_summary = ", ".join([cf.get("label", "") for cf in counterfactuals[:3]]) if counterfactuals else "None identified"
            rules_summary = ", ".join([r.get("rule_id", "") for r in rules[:5]]) if rules else "None"
            
            prompt = (
                "You are the Gold Team XAI agent. Summarize the decision and evidence in 2-3 sentences. "
                "Include context about counterfactuals and triggered rules. Keep it synthetic and defensive.\n\n"
                f"Decision: {decision}\n"
                f"Evidence count: {len(evidence_items)}\n"
                f"Triggered rules: {rules_summary}\n"
                f"Top counterfactuals: {cf_summary}"
            )
            summary = await llm_client.chat_completions_create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You provide concise fraud-defense explanations."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
            )
            bundle.summary = summary.strip()
            bundle.details = f"LLM-derived explanation based on {len(evidence_items)} evidence items and {len(counterfactuals)} counterfactuals."
            bundle.confidence_statement = "Confidence reflects LLM reasoning with evidence-linked counterfactuals."
            
            # Generate enhanced counterfactual explanations
            for cf in counterfactuals[:2]:
                try:
                    enhanced_desc = await cf_service.generate_llm_counterfactual_explanation(
                        cf, context=f"Decision: {decision}, Rules: {rules_summary}"
                    )
                    if enhanced_desc:
                        cf["description"] = enhanced_desc
                except Exception:
                    pass
        except Exception:
            pass

    # Find similar cases from evidence packs
    packs = await db.evidence_packs.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Build current case signature
    current_signature = sc_service.build_case_signature(
        run_id, decision, evidence_items, events, run_metrics
    )
    
    # Find similar cases using enhanced service
    similar_cases = await sc_service.find_similar_cases(
        current_signature, packs, exclude_run_id=run_id, min_similarity=0.2, max_results=5
    )
    bundle.similar_cases = similar_cases

    # Record events and audit
    await record_run_event(
        run_id,
        "xai.generated",
        {
            "decision": decision,
            "bundle_id": bundle.bundle_id,
            "evidence_count": len(evidence_items),
            "counterfactual_count": len(counterfactuals),
            "similar_cases": len(similar_cases),
            "features_extracted": len(features),
            "rules_extracted": len(rules),
        },
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "xai.bundle.generated",
        "run",
        run_id,
        metadata={
            "bundle_id": bundle.bundle_id,
            "evidence_links": [f"xai_bundle:{bundle.bundle_id}"],
            "counterfactual_count": len(counterfactuals),
            "similar_case_count": len(similar_cases),
        },
    )
    logger.info(
        "xai.bundle.generated",
        extra={
            "payload": {
                "run_id": run_id,
                "evidence": len(evidence_items),
                "counterfactuals": len(counterfactuals),
                "similar_cases": len(similar_cases),
            }
        },
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
    """Generate UI commentary text with self-learning.

    Args:
        payload: Commentary payload.
        llm_client: Optional LLM client.

    Returns:
        CommentorResponse: Generated commentary.
    """
    from app.core.agent_learning import LEARNING_ENGINE
    
    now = datetime.now(timezone.utc).isoformat()
    highlights = ", ".join(payload.highlights[:6]) if payload.highlights else "key activity updates"
    
    # Self-Learning: Recall
    lessons = await LEARNING_ENGINE.recall_lessons("commentor", "gold", f"{payload.screen} {payload.role}")
    lesson_context = ""
    if lessons:
        lesson_context = "\nPast successful commentaries:\n" + "\n".join(
            [f"- {l['content']}" for l in lessons]
        )

    prompt = (
        "You are MIRA (Multi-purpose Intelligent Response Agent), the AI assistant for Fraud Forge. "
        "Describe what is happening on the current screen in 2-3 concise sentences, confident and helpful tone. "
        "Do not invent sensitive identifiers or personal data. "
        f"{lesson_context}\n"
        f"Screen: {payload.screen}. Role: {payload.role}. "
        f"Summary: {payload.summary or 'Operational overview.'}. "
        f"Highlights: {highlights}."
    )

    if llm_client:
        try:
            model_name = get_integration_setting("llm", "model", "gpt-4o") or "gpt-4o"
            text = await llm_client.chat_completions_create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You provide safe, concise UI commentary."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=120,
            )
            text = text.strip()
            # Record lesson
            await LEARNING_ENGINE.record_lesson(
                agent_id="commentor",
                team_id="gold",
                task_type=payload.screen,
                content=text,
                outcome="success",
                confidence=0.9
            )
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


class CounterfactualRequest(BaseModel):
    run_id: str
    decision: Optional[str] = None
    max_counterfactuals: int = Field(default=5, le=10)


class CounterfactualResponse(BaseModel):
    run_id: str
    decision: str
    counterfactuals: List[Dict[str, Any]]
    features_used: int
    rules_used: int
    generated_at: str


class SimilarCasesRequest(BaseModel):
    run_id: str
    min_similarity: float = Field(default=0.2, ge=0.0, le=1.0)
    max_results: int = Field(default=5, le=20)


class SimilarCasesResponse(BaseModel):
    run_id: str
    similar_cases: List[Dict[str, Any]]
    signature_hash: str
    generated_at: str


@router.post("/xai/counterfactuals", response_model=CounterfactualResponse)
async def generate_counterfactuals(
    payload: CounterfactualRequest,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
):
    """Generate counterfactuals for a run.

    This endpoint generates feature-based and rule-based counterfactuals
    linked to real evidence items from the run's telemetry.

    Args:
        payload: Request with run_id and optional settings.
        db: Database client.
        llm_client: Optional LLM client for enhanced explanations.

    Returns:
        CounterfactualResponse: Generated counterfactuals with evidence links.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": payload.run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = payload.decision or run.get("last_decision", "monitor")
    run_metrics = run.get("last_metrics", {})
    events = await db.run_events.find({"run_id": payload.run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)

    # Initialize service and generate counterfactuals
    cf_service = CounterfactualService(db_client=db, llm_client=llm_client)
    features = cf_service.extract_features_from_evidence(evidence_items)
    rules = cf_service.extract_rules_from_evidence(evidence_items, events)
    counterfactuals = cf_service.generate_combined_counterfactuals(
        features, rules, decision, run_metrics
    )

    # Limit to requested count
    counterfactuals = counterfactuals[:payload.max_counterfactuals]

    # Enhance with LLM if available
    if llm_client:
        for cf in counterfactuals[:2]:
            try:
                rules_summary = ", ".join([r.get("rule_id", "") for r in rules[:5]]) if rules else "None"
                enhanced_desc = await cf_service.generate_llm_counterfactual_explanation(
                    cf, context=f"Decision: {decision}, Rules: {rules_summary}"
                )
                if enhanced_desc:
                    cf["description"] = enhanced_desc
            except Exception:
                pass

    await record_audit(
        current_user.get("id", "unknown"),
        "xai.counterfactuals.generated",
        "run",
        payload.run_id,
        metadata={
            "decision": decision,
            "count": len(counterfactuals),
            "features": len(features),
            "rules": len(rules),
        },
    )
    logger.info(
        "xai.counterfactuals.generated",
        extra={
            "payload": {
                "run_id": payload.run_id,
                "decision": decision,
                "counterfactuals": len(counterfactuals),
            }
        },
    )

    return CounterfactualResponse(
        run_id=payload.run_id,
        decision=decision,
        counterfactuals=counterfactuals,
        features_used=len(features),
        rules_used=len(rules),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/xai/similar-cases", response_model=SimilarCasesResponse)
async def find_similar_cases(
    payload: SimilarCasesRequest,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
):
    """Find similar cases for a run based on evidence pack matching.

    This endpoint uses evidence pack signatures to find historically similar
    cases with detailed similarity breakdowns and rule matching.

    Args:
        payload: Request with run_id and similarity settings.
        db: Database client.

    Returns:
        SimilarCasesResponse: Similar cases with detailed similarity scores.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": payload.run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    decision = run.get("last_decision", "monitor")
    run_metrics = run.get("last_metrics", {})
    events = await db.run_events.find({"run_id": payload.run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    evidence_items = build_evidence_items(events)

    # Initialize service and build signature
    sc_service = SimilarCaseService(db_client=db)
    current_signature = sc_service.build_case_signature(
        payload.run_id, decision, evidence_items, events, run_metrics
    )

    # Find similar cases from evidence packs
    packs = await db.evidence_packs.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    similar_cases = await sc_service.find_similar_cases(
        current_signature,
        packs,
        exclude_run_id=payload.run_id,
        min_similarity=payload.min_similarity,
        max_results=payload.max_results,
    )

    await record_audit(
        current_user.get("id", "unknown"),
        "xai.similar_cases.retrieved",
        "run",
        payload.run_id,
        metadata={
            "count": len(similar_cases),
            "min_similarity": payload.min_similarity,
            "signature_hash": current_signature.get("signature_hash"),
        },
    )
    logger.info(
        "xai.similar_cases.retrieved",
        extra={
            "payload": {
                "run_id": payload.run_id,
                "similar_cases": len(similar_cases),
            }
        },
    )

    return SimilarCasesResponse(
        run_id=payload.run_id,
        similar_cases=similar_cases,
        signature_hash=current_signature.get("signature_hash", ""),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/xai/evidence-pack/{pack_id}/similar")
async def find_similar_to_pack(
    pack_id: str,
    min_similarity: float = 0.2,
    max_results: int = 5,
    current_user: dict = Depends(require_permission("xai:read")),
    db: DatabaseClient = Depends(get_db),
):
    """Find similar cases to an existing evidence pack.

    Args:
        pack_id: Evidence pack identifier.
        min_similarity: Minimum similarity threshold.
        max_results: Maximum number of results.
        db: Database client.

    Returns:
        dict: Similar cases with pack signature.

    Raises:
        HTTPException: If evidence pack is not found.
    """
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")

    sc_service = SimilarCaseService(db_client=db)
    current_signature = sc_service.build_pack_signature(pack)

    # Find similar packs
    packs = await db.evidence_packs.find({"id": {"$ne": pack_id}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    similar_cases = await sc_service.find_similar_cases(
        current_signature,
        packs,
        exclude_run_id=pack.get("run_id"),
        min_similarity=min_similarity,
        max_results=max_results,
    )

    await record_audit(
        current_user.get("id", "unknown"),
        "xai.pack_similar.retrieved",
        "evidence_pack",
        pack_id,
        metadata={"count": len(similar_cases)},
    )

    return {
        "pack_id": pack_id,
        "signature": current_signature,
        "similar_cases": similar_cases,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

