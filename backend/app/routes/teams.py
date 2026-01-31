from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import TeamProfile
from app.teams_data import default_team_payloads

router = APIRouter()

@router.get("/teams")
async def list_teams():
    teams = await db.teams.find({}, {"_id": 0}).to_list(50)
    if not teams:
        for payload in default_team_payloads():
            team = TeamProfile(**payload)
            await db.teams.insert_one(team.model_dump())
        teams = await db.teams.find({}, {"_id": 0}).to_list(50)
    return teams

@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    team = await db.teams.find_one({"team_id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/teams/seed")
async def seed_teams():
    existing = await db.teams.count_documents({})
    if existing:
        return {"message": "Teams already seeded", "count": existing}
    payloads = default_team_payloads()
    teams = [TeamProfile(**payload).model_dump() for payload in payloads]
    if teams:
        await db.teams.insert_many(teams)
    return {"message": "Teams seeded", "count": len(teams)}
