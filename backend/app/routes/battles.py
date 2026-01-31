from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
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
