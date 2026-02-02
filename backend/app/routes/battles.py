"""Battle lifecycle routes.

Provides CRUD and import operations for battles.
"""

from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from app.db import db
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.models import Battle, BattleCreate
from app.security import require_permission
from app.services.capsules.brc.brc_service import import_brc_bytes, persist_brc_package

router = APIRouter()
logger = get_logger(__name__)

@router.get("/battles")
async def get_battles(current_user: dict = Depends(require_permission("battle:read"))) -> List[Dict]:
    """List battles.

    Args:
        current_user: Authorized user context.

    Returns:
        List[Dict]: Battles list.

    Raises:
        None: No explicit exceptions are raised.
    """
    battles = await db.battles.find({}, {"_id": 0}).to_list(100)
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.list",
        "battle",
        "list",
    )
    return battles

@router.get("/battles/{battle_id}")
async def get_battle(battle_id: str, current_user: dict = Depends(require_permission("battle:read"))) -> Dict:
    """Get a battle by ID.

    Args:
        battle_id: Battle identifier.
        current_user: Authorized user context.

    Returns:
        Dict: Battle document.

    Raises:
        HTTPException: If battle is not found.
    """
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.read",
        "battle",
        battle_id,
    )
    return battle

@router.post("/battles")
async def create_battle(battle_data: BattleCreate, current_user: dict = Depends(require_permission("battle:write"))) -> Battle:
    """Create a battle.

    Args:
        battle_data: Battle creation payload.
        current_user: Authorized user context.

    Returns:
        Battle: Created battle.

    Raises:
        None: No explicit exceptions are raised.
    """
    battle = Battle(scenario_name=battle_data.scenario_name, parameters=battle_data.parameters)
    await db.battles.insert_one(battle.model_dump())
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.created",
        "battle",
        battle.id,
        metadata={"scenario": battle.scenario_name},
    )
    logger.info("battle.created", extra={"payload": {"battle_id": battle.id, "scenario": battle.scenario_name}})
    return battle

@router.post("/battles/{battle_id}/start")
async def start_battle(battle_id: str, current_user: dict = Depends(require_permission("battle:write"))) -> Dict:
    """Start a battle.

    Args:
        battle_id: Battle identifier.
        current_user: Authorized user context.

    Returns:
        Dict: Updated battle.

    Raises:
        HTTPException: If battle is not found.
    """
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "running"}})
    battle["status"] = "running"
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.started",
        "battle",
        battle_id,
    )
    logger.info("battle.started", extra={"payload": {"battle_id": battle_id}})
    return battle

@router.post("/battles/{battle_id}/stop")
async def stop_battle(battle_id: str, current_user: dict = Depends(require_permission("battle:write"))) -> Dict:
    """Stop a battle.

    Args:
        battle_id: Battle identifier.
        current_user: Authorized user context.

    Returns:
        Dict: Updated battle.

    Raises:
        HTTPException: If battle is not found.
    """
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    completed_at = datetime.now(timezone.utc).isoformat()
    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "completed", "completed_at": completed_at}})
    battle["status"] = "completed"
    battle["completed_at"] = completed_at
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.stopped",
        "battle",
        battle_id,
        metadata={"completed_at": completed_at},
    )
    logger.info("battle.completed", extra={"payload": {"battle_id": battle_id}})
    return battle

@router.delete("/battles/{battle_id}")
async def delete_battle(battle_id: str, current_user: dict = Depends(require_permission("battle:write"))) -> Dict[str, str]:
    """Delete a battle.

    Args:
        battle_id: Battle identifier.
        current_user: Authorized user context.

    Returns:
        Dict[str, str]: Deletion result.

    Raises:
        HTTPException: If battle is not found.
    """
    result = await db.battles.delete_one({"id": battle_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Battle not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.deleted",
        "battle",
        battle_id,
    )
    logger.info("battle.deleted", extra={"payload": {"battle_id": battle_id}})
    return {"message": "Battle deleted"}

@router.post("/battles/import-brc")
async def import_brc(file: UploadFile = File(...), current_user: dict = Depends(require_permission("battle:write"))) -> Battle:
    """Import a BRC archive into a battle.

    Args:
        file: Uploaded BRC archive.
        current_user: Authorized user context.

    Returns:
        Battle: Imported battle.

    Raises:
        HTTPException: If archive is invalid.
    """
    content = await file.read()
    try:
        import_report = import_brc_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    manifest = import_report.get("manifest") or {}
    battle_type = import_report.get("battle_type", "Imported Battle")
    run_id = import_report.get("run_id", "imported")

    await persist_brc_package(content, manifest, current_user.get("id", "unknown"), status="imported")

    turns = import_report.get("turns") or [
        {
            "red_team": {"action": "synthetic", "success": True},
            "blue_team": {"action": "review", "blocked": True},
        }
    ]

    battle = Battle(
        scenario_name=battle_type,
        status="completed",
        turns=turns,
        parameters={"imported_from": run_id, "source": "brc"},
        metrics={
            "success_rate": 100,
            "money_at_risk": 0,
            "money_saved": 0,
            "time_to_immunity": 0,
            "patterns_learned": 0,
        },
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    await db.battles.insert_one(battle.model_dump())
    await record_audit(
        current_user.get("id", "unknown"),
        "battle.imported",
        "battle",
        battle.id,
        metadata={"scenario": battle.scenario_name, "source": "brc", "run_id": run_id},
    )
    logger.info(
        "battle.imported",
        extra={"payload": {"battle_id": battle.id, "scenario": battle.scenario_name, "source": "brc"}},
    )
    return battle
