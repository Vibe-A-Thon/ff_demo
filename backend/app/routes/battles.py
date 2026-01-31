from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File
import io
import json
import zipfile
from app.db import db
from app.models import Battle, BattleCreate

router = APIRouter()

@router.get("/battles")
async def get_battles():
    battles = await db.battles.find({}, {"_id": 0}).to_list(100)
    return battles

@router.get("/battles/{battle_id}")
async def get_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    return battle

@router.post("/battles")
async def create_battle(battle_data: BattleCreate):
    battle = Battle(scenario_name=battle_data.scenario_name, parameters=battle_data.parameters)
    await db.battles.insert_one(battle.model_dump())
    return battle

@router.post("/battles/{battle_id}/start")
async def start_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "running"}})
    battle["status"] = "running"
    return battle

@router.post("/battles/{battle_id}/stop")
async def stop_battle(battle_id: str):
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")

    completed_at = datetime.now(timezone.utc).isoformat()
    await db.battles.update_one({"id": battle_id}, {"$set": {"status": "completed", "completed_at": completed_at}})
    battle["status"] = "completed"
    battle["completed_at"] = completed_at
    return battle

@router.delete("/battles/{battle_id}")
async def delete_battle(battle_id: str):
    result = await db.battles.delete_one({"id": battle_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Battle not found")
    return {"message": "Battle deleted"}

@router.post("/battles/import-brc")
async def import_brc(file: UploadFile = File(...)):
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
    return battle
