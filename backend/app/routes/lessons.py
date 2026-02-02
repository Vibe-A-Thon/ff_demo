"""Lesson Distiller API routes - Convert BRC/battle learnings to AMC format."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.security import require_permission
from app.services.capsules.amc.lesson_distiller import lesson_distiller

router = APIRouter()
logger = get_logger(__name__)


@router.post("/lessons/distill-battle")
async def distill_battle_learnings(
    battle_id: str = Form(...),
    team_id: str = Form(...),
    current_user: dict = Depends(require_permission("amc:write")),
):
    """
    Distill learnings from a completed battle into AMC-compatible memory entries.
    
    This converts raw battle outcomes into:
    - Semantic memory entries (facts/knowledge)
    - Episodic memory entries (experiences)
    - Markdown summary for judges
    """
    try:
        result = await lesson_distiller.distill_battle_outcome(
            battle_id=battle_id,
            team_id=team_id,
            actor_id=current_user.get("id", "unknown"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    await record_audit(
        current_user.get("id", "unknown"),
        "lessons.distilled_battle",
        "battle",
        battle_id,
        metadata={"team_id": team_id, "semantic_count": result["stats"]["semantic_count"]},
    )
    
    logger.info(
        "lessons.distilled_battle",
        extra={"payload": {"battle_id": battle_id, "team_id": team_id}},
    )
    
    return result


@router.post("/lessons/distill-brc")
async def distill_brc_postmortem(
    brc_id: str = Form(...),
    team_id: str = Form(...),
    current_user: dict = Depends(require_permission("amc:write")),
):
    """
    Distill learnings from a BRC postmortem into AMC-compatible entries.
    
    This converts lessons learned, improvements, and recommendations into:
    - Semantic memory entries
    - Episodic memory entries
    - Procedural updates
    """
    try:
        result = await lesson_distiller.distill_brc_postmortem(
            brc_id=brc_id,
            team_id=team_id,
            actor_id=current_user.get("id", "unknown"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    await record_audit(
        current_user.get("id", "unknown"),
        "lessons.distilled_brc",
        "brc",
        brc_id,
        metadata={"team_id": team_id, "semantic_count": result["stats"]["semantic_count"]},
    )
    
    logger.info(
        "lessons.distilled_brc",
        extra={"payload": {"brc_id": brc_id, "team_id": team_id}},
    )
    
    return result


@router.get("/lessons/team/{team_id}")
async def get_team_distilled_lessons(
    team_id: str,
    since_days: int = 180,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """
    Get all distilled lessons for a team within a time window.
    
    Used for AMC export to populate memory layers.
    """
    result = await lesson_distiller.get_distilled_lessons_for_team(
        team_id=team_id,
        since_days=since_days,
    )
    
    await record_audit(
        current_user.get("id", "unknown"),
        "lessons.retrieved",
        "team",
        team_id,
        metadata={"since_days": since_days},
    )
    
    return result


@router.get("/lessons/distillations")
async def list_distillations(
    team_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """
    List distillation records with optional team filter.
    """
    from app.db import db
    
    query = {}
    if team_id:
        query["team_id"] = team_id
    
    cursor = db.lesson_distillations.find(query, {"_id": 0}).sort("distilled_at", -1).limit(limit)
    records = await cursor.to_list(length=limit)
    
    return {"distillations": records, "count": len(records)}
