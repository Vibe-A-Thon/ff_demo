"""Team profile routes.

Provides team listing and seeding utilities.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.models import TeamProfile
from app.teams_data import default_team_payloads
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/teams")
async def list_teams(current_user: dict = Depends(require_permission("teams:read"))):
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
        await record_audit(
            current_user.get("id", "unknown"),
            "teams.seeded",
            "team",
            "seed",
            metadata={"count": len(teams)},
        )
    await record_audit(
        current_user.get("id", "unknown"),
        "teams.list",
        "team",
        "list",
    )
    return teams

@router.get("/teams/{team_id}")
async def get_team(team_id: str, current_user: dict = Depends(require_permission("teams:read"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "teams.read",
        "team",
        team_id,
    )
    return team

@router.post("/teams/seed")
async def seed_teams(current_user: dict = Depends(require_permission("teams:write"))):
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
        await record_audit(
            current_user.get("id", "unknown"),
            "teams.seed.skipped",
            "team",
            "seed",
            metadata={"count": existing},
        )
        return {"message": "Teams already seeded", "count": existing}
    payloads = default_team_payloads()
    teams = [TeamProfile(**payload).model_dump() for payload in payloads]
    if teams:
        await db.teams.insert_many(teams)
    logger.info("teams.seeded", extra={"payload": {"count": len(teams)}})
    await record_audit(
        current_user.get("id", "unknown"),
        "teams.seeded",
        "team",
        "seed",
        metadata={"count": len(teams)},
    )
    return {"message": "Teams seeded", "count": len(teams)}
