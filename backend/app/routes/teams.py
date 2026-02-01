"""Team profile routes.

Provides team listing and seeding utilities.
"""

from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import TeamProfile
from app.teams_data import default_team_payloads
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/teams")
async def list_teams():
    """List team profiles, seeding defaults if empty.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        list[dict]: Team profiles.

    Raises:
        None: No explicit exceptions are raised.
    """
    teams = await db.teams.find({}, {"_id": 0}).to_list(50)
    if not teams:
        for payload in default_team_payloads():
            team = TeamProfile(**payload)
            await db.teams.insert_one(team.model_dump())
        teams = await db.teams.find({}, {"_id": 0}).to_list(50)
        logger.info("teams.seeded", extra={"payload": {"count": len(teams)}})
    return teams

@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    """Get a single team profile.

    Args:
        team_id: Team identifier.

    Returns:
        dict: Team profile.

    Raises:
        HTTPException: If the team does not exist.
    """
    team = await db.teams.find_one({"team_id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/teams/seed")
async def seed_teams():
    """Seed default teams if none exist.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        dict: Seeding result.

    Raises:
        None: No explicit exceptions are raised.
    """
    existing = await db.teams.count_documents({})
    if existing:
        logger.info("teams.seed.skipped", extra={"payload": {"count": existing}})
        return {"message": "Teams already seeded", "count": existing}
    payloads = default_team_payloads()
    teams = [TeamProfile(**payload).model_dump() for payload in payloads]
    if teams:
        await db.teams.insert_many(teams)
    logger.info("teams.seeded", extra={"payload": {"count": len(teams)}})
    return {"message": "Teams seeded", "count": len(teams)}
