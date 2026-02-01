"""Battle lifecycle routes.

Provides CRUD and import operations for battles.
"""

from datetime import datetime, timezone
from typing import Dict, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
import io
import json
import zipfile
from app.db import db
from app.core.logging_config import get_logger
from app.models import Battle, BattleCreate
from app.security import require_permission

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
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Invalid BRC archive") from exc

    manifest = {}
    if "manifest.json" in archive.namelist():
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    battle_type = manifest.get("battle_type", "Imported Battle")
    run_id = manifest.get("run_id", "imported")

    red_output = {}
    blue_output = {}
    for name in archive.namelist():
        if not name.endswith(".json") or name == "manifest.json":
            continue
        data = json.loads(archive.read(name).decode("utf-8"))
        team = (data.get("team") or "").lower()
        if team == "red" and not red_output:
            red_output = data
        if team == "blue" and not blue_output:
            blue_output = data

    turn = {
        "red_team": {
            "action": (red_output.get("outputs") or {}).get("attack_plan", {}).get("campaign", "synthetic"),
            "success": True,
        },
        "blue_team": {
            "action": (blue_output.get("outputs") or {}).get("decision", {}).get("outcome", "review"),
            "blocked": True,
        },
    }

    battle = Battle(
        scenario_name=battle_type,
        status="completed",
        turns=[turn],
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
    logger.info(
        "battle.imported",
        extra={"payload": {"battle_id": battle.id, "scenario": battle.scenario_name, "source": "brc"}},
    )
    return battle
