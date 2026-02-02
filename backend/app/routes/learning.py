"""
Learning Loop API Routes

Provides endpoints for the "Never Fail Twice" learning mechanism:
- POST /api/learn-from-battle/{battle_id} - Learn from a completed battle
- GET /api/immunity/score - Get current immunity score
- POST /api/immunity/check - Check immunity against an attack vector
- POST /api/seed/full-roster - Seed the full 54-agent roster
- POST /api/seed/rag-collections - Seed all 5 RAG collections
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from app.core.external_services import DatabaseClient, LLMClient
from app.dependencies import get_db, get_llm_client
from app.security import require_permission
from app.core.logging_config import get_logger
from app.services.learning_loop import LearningLoopService
from app.services.multi_collection_rag import MultiCollectionRAGService

logger = get_logger(__name__)
router = APIRouter(tags=["learning"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AttackVector(BaseModel):
    """Attack vector details for learning."""
    attack_type: str = Field(..., description="Type of attack (e.g., velocity, ato, identity)")
    entry_vector: str = Field(default="unknown", description="Entry point of the attack")
    target: str = Field(default="unknown", description="Target of the attack")
    technique: str = Field(default="unknown", description="Technique used")
    indicators: List[str] = Field(default_factory=list, description="Attack indicators")
    payload: Optional[str] = Field(default=None, description="Attack payload pattern")


class DefenseSignature(BaseModel):
    """Defense signature details."""
    method: str = Field(default="rule_match", description="Detection method used")
    confidence: float = Field(default=0.0, description="Detection confidence (0-1)")
    rules_triggered: List[str] = Field(default_factory=list, description="Rules that triggered")
    indicators_detected: List[str] = Field(default_factory=list, description="Indicators detected")


class LearnFromBattleRequest(BaseModel):
    """Request to learn from a battle."""
    winner: str = Field(..., description="Winner of the battle: 'red' or 'blue'")
    attack_vector: AttackVector
    defense_signature: Optional[DefenseSignature] = None
    metadata: Optional[Dict[str, Any]] = None


class ImmunityCheckRequest(BaseModel):
    """Request to check immunity against an attack."""
    attack_vector: AttackVector


# ============================================================================
# Learning Loop Endpoints
# ============================================================================

@router.post("/learn-from-battle/{battle_id}")
async def learn_from_battle(
    battle_id: str,
    request: LearnFromBattleRequest,
    current_user: dict = Depends(require_permission("battles:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Learn from a completed battle and store the outcome.
    
    This is the core "Never Fail Twice" endpoint. After each battle:
    - If Red wins: Attack vector is stored in 'attacks' collection
    - If Blue wins: Defense pattern is stored in 'patterns' collection
    
    Args:
        battle_id: Unique battle identifier
        request: Battle outcome details
        
    Returns:
        Learning result with document IDs created
    """
    if request.winner not in ("red", "blue"):
        raise HTTPException(status_code=400, detail="Winner must be 'red' or 'blue'")
    
    service = LearningLoopService(db, llm_client)
    
    try:
        result = await service.learn_from_battle(
            battle_id=battle_id,
            winner=request.winner,
            attack_vector=request.attack_vector.model_dump(),
            defense_signature=request.defense_signature.model_dump() if request.defense_signature else None,
            metadata=request.metadata
        )
        
        logger.info(
            "api.learn.completed",
            extra={"payload": {"battle_id": battle_id, "winner": request.winner}}
        )
        
        return {
            "status": "learned",
            "battle_id": battle_id,
            **result
        }
        
    except Exception as e:
        logger.error(
            "api.learn.failed",
            extra={"payload": {"battle_id": battle_id, "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/immunity/score")
async def get_immunity_score(
    current_user: dict = Depends(require_permission("metrics:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Get the current immunity score.
    
    Returns metrics on how well the system has learned from past attacks.
    """
    service = LearningLoopService(db, llm_client)
    return await service.get_immunity_score()


@router.post("/immunity/check")
async def check_immunity(
    request: ImmunityCheckRequest,
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Check if the system has immunity against a specific attack vector.
    
    Returns whether matching defense patterns exist and their confidence.
    """
    service = LearningLoopService(db, llm_client)
    return await service.check_immunity(request.attack_vector.model_dump())


# ============================================================================
# Seeding Endpoints
# ============================================================================

@router.post("/seed/full-roster")
async def seed_full_roster(
    reset: bool = False,
    current_user: dict = Depends(require_permission("admin:write")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """
    Seed the full 54-agent roster (8 teams).
    
    Args:
        reset: If True, clears existing teams and agents first
        
    Returns:
        Seeding results with counts
    """
    from app.seed_data.full_roster_generator import generate_full_roster, get_team_summary
    
    try:
        if reset:
            await db.teams.delete_many({})
            await db.agents.delete_many({})
        
        roster = generate_full_roster()
        
        # Insert teams
        teams_inserted = 0
        for team in roster["teams"]:
            await db.teams.update_one(
                {"team_id": team["team_id"]},
                {"$set": team},
                upsert=True
            )
            teams_inserted += 1
        
        # Insert agents
        agents_inserted = 0
        for agent in roster["agents"]:
            await db.agents.update_one(
                {"agent_id": agent["agent_id"]},
                {"$set": agent},
                upsert=True
            )
            agents_inserted += 1
        
        summary = get_team_summary()
        
        logger.info(
            "api.seed.roster.completed",
            extra={"payload": {"teams": teams_inserted, "agents": agents_inserted}}
        )
        
        return {
            "status": "completed",
            "reset": reset,
            "teams_seeded": teams_inserted,
            "agents_seeded": agents_inserted,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(
            "api.seed.roster.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed/rag-collections")
async def seed_rag_collections(
    reset: bool = False,
    include_taxonomy: bool = True,
    current_user: dict = Depends(require_permission("rag:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Seed all 5 RAG collections with default content and taxonomy.
    
    Args:
        reset: If True, clears existing RAG documents first
        include_taxonomy: If True, seeds the 120-scenario taxonomy
        
    Returns:
        Seeding results for each collection
    """
    try:
        if reset:
            await db.rag_documents.delete_many({})
            await db.rag_collection_meta.delete_many({})
        
        service = MultiCollectionRAGService(db, llm_client)
        
        # Initialize collections
        init_result = await service.initialize_collections()
        
        # Seed default documents
        defaults_result = await service.seed_default_documents()
        
        # Seed taxonomy if requested
        taxonomy_result = None
        if include_taxonomy:
            taxonomy_result = await service.seed_taxonomy()
        
        # Get stats
        stats = await service.get_collection_stats()
        
        logger.info(
            "api.seed.rag.completed",
            extra={"payload": {"reset": reset, "include_taxonomy": include_taxonomy}}
        )
        
        return {
            "status": "completed",
            "reset": reset,
            "collections_initialized": init_result,
            "defaults_seeded": defaults_result,
            "taxonomy_seeded": taxonomy_result,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(
            "api.seed.rag.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/collections/stats")
async def get_rag_collection_stats(
    current_user: dict = Depends(require_permission("rag:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Get statistics for all 5 RAG collections.
    """
    service = MultiCollectionRAGService(db, llm_client)
    return await service.get_collection_stats()


@router.post("/seed/complete")
async def seed_complete_demo(
    reset: bool = False,
    current_user: dict = Depends(require_permission("admin:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Complete demo seeding: Full roster + All RAG collections.
    
    This is the one-stop endpoint to prepare the entire demo dataset.
    """
    from app.seed_data.full_roster_generator import generate_full_roster, get_team_summary
    from app.seed_data.demo_data_generator import generate_demo_data
    
    results = {}
    
    try:
        if reset:
            # Clear all collections
            await db.teams.delete_many({})
            await db.agents.delete_many({})
            await db.rag_documents.delete_many({})
            await db.rag_collection_meta.delete_many({})
            await db.battles.delete_many({})
            await db.rules.delete_many({})
            await db.learning_events.delete_many({})
        
        # 1. Seed full roster
        roster = generate_full_roster()
        for team in roster["teams"]:
            await db.teams.update_one({"team_id": team["team_id"]}, {"$set": team}, upsert=True)
        for agent in roster["agents"]:
            await db.agents.update_one({"agent_id": agent["agent_id"]}, {"$set": agent}, upsert=True)
        
        results["roster"] = {
            "teams": len(roster["teams"]),
            "agents": len(roster["agents"])
        }
        
        # 2. Seed RAG collections
        rag_service = MultiCollectionRAGService(db, llm_client)
        await rag_service.initialize_collections()
        await rag_service.seed_default_documents()
        taxonomy_result = await rag_service.seed_taxonomy()
        
        results["rag"] = {
            "taxonomy_scenarios": taxonomy_result.get("seeded", 0),
            "defaults_seeded": True
        }
        
        # 3. Seed demo data (battles, rules, etc.)
        demo_data = generate_demo_data()
        
        for rule in demo_data.get("rules", []):
            await db.rules.insert_one(rule)
        
        for battle in demo_data.get("battles", []):
            await db.battles.insert_one(battle)
        
        results["demo"] = {
            "rules": len(demo_data.get("rules", [])),
            "battles": len(demo_data.get("battles", []))
        }
        
        # Get final stats
        stats = await rag_service.get_collection_stats()
        
        logger.info(
            "api.seed.complete.completed",
            extra={"payload": results}
        )
        
        return {
            "status": "completed",
            "reset": reset,
            "seeded": results,
            "rag_stats": stats
        }
        
    except Exception as e:
        logger.error(
            "api.seed.complete.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))
