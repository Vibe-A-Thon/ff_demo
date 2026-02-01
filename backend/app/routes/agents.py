"""Agent registry and task routes."""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.agent_registry import AgentRegistry
from app.models import AgentProfile, AgentProfileCreate, AgentRequest, AgentRequestCreate, AgentRequestDecision, AgentResult, AgentTask
from app.rag_utils import contains_sensitive_identifiers
from app.teams_data import default_agent_payloads
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)
DEFAULT_REGISTRY = AgentRegistry.from_defaults()

@router.get("/agents")
async def list_agents(team_id: str | None = None):
    """List agents, optionally filtered by team.

    Args:
        team_id: Optional team identifier.

    Returns:
        list[dict]: Agent profiles.

    Raises:
        None: No explicit exceptions are raised.
    """
    query = {}
    if team_id:
        query["team_id"] = team_id
    agents = await db.agents.find(query, {"_id": 0}).to_list(200)
    if agents:
        return agents
    return [agent.model_dump() for agent in DEFAULT_REGISTRY.list_agents(team_id)]

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a single agent profile.

    Args:
        agent_id: Agent identifier.

    Returns:
        dict: Agent profile.

    Raises:
        HTTPException: If the agent does not exist.
    """
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        fallback = DEFAULT_REGISTRY.get_agent(agent_id)
        if fallback:
            return fallback.model_dump()
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.get("/agents/registry")
async def get_registry_snapshot(team_id: str | None = None):
    """Return registry snapshot and delegation preview.

    Args:
        team_id: Optional team identifier.

    Returns:
        dict: Teams, agents, and delegation preview.

    Raises:
        None: No explicit exceptions are raised.
    """
    teams = [team.model_dump() for team in DEFAULT_REGISTRY.list_teams()]
    agents = [agent.model_dump() for agent in DEFAULT_REGISTRY.list_agents(team_id)]
    preview_team = team_id or (teams[0]["team_id"] if teams else None)
    delegation_preview = (
        DEFAULT_REGISTRY.build_delegation_plan(preview_team, "Registry preview") if preview_team else []
    )
    return {"teams": teams, "agents": agents, "delegation_preview": delegation_preview}

@router.post("/agents/register")
async def register_agent(agent_data: AgentProfileCreate):
    """Register a new agent profile.

    Args:
        agent_data: Agent profile payload.

    Returns:
        AgentProfile: Created agent profile.

    Raises:
        None: No explicit exceptions are raised.
    """
    profile = AgentProfile(**agent_data.model_dump())
    await db.agents.insert_one(profile.model_dump())
    logger.info("agent.registered", extra={"payload": {"agent_id": profile.agent_id, "team_id": profile.team_id}})
    return profile

@router.post("/agents/seed")
async def seed_agents():
    """Seed default agents into storage.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        dict: Seeding result.

    Raises:
        None: No explicit exceptions are raised.
    """
    payloads = default_agent_payloads()
    inserted = 0
    for payload in payloads:
        agent_id = payload.get("agent_id")
        if agent_id:
            exists = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
            if exists:
                continue
        profile = AgentProfile(**payload)
        await db.agents.insert_one(profile.model_dump())
        inserted += 1
    total = await db.agents.count_documents({})
    logger.info("agents.seeded", extra={"payload": {"inserted": inserted, "total": total}})
    return {"message": "Agents seeded", "count": total, "inserted": inserted}

@router.post("/agents/tasks")
async def create_agent_task(task_data: AgentTask):
    """Create an agent task.

    Args:
        task_data: Task payload.

    Returns:
        AgentTask: Created task.

    Raises:
        HTTPException: If synthetic-only validation fails.
    """
    if task_data.inputs:
        joined = __import__("json").dumps(task_data.inputs, default=str)
        if contains_sensitive_identifiers(joined):
            raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    await db.agent_tasks.insert_one(task_data.model_dump())
    logger.info(
        "agent.task.created",
        extra={"payload": {"task_id": task_data.task_id, "team_id": task_data.team_id, "run_id": task_data.run_id}},
    )
    return task_data

@router.get("/agents/tasks")
async def list_agent_tasks(run_id: str | None = None, team_id: str | None = None, status_filter: str | None = None):
    """List agent tasks.

    Args:
        run_id: Optional run identifier.
        team_id: Optional team identifier.
        status_filter: Optional status filter.

    Returns:
        list[dict]: Agent tasks.

    Raises:
        None: No explicit exceptions are raised.
    """
    query = {}
    if run_id:
        query["run_id"] = run_id
    if team_id:
        query["team_id"] = team_id
    if status_filter:
        query["status"] = status_filter
    tasks = await db.agent_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return tasks

@router.post("/agents/tasks/{task_id}/complete")
async def complete_agent_task(task_id: str, result: AgentResult):
    """Complete an agent task.

    Args:
        task_id: Task identifier.
        result: Task result payload.

    Returns:
        AgentResult: Persisted result.

    Raises:
        HTTPException: If the task does not exist.
    """
    task = await db.agent_tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.agent_tasks.update_one(
        {"task_id": task_id},
        {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    logger.info(
        "agent.task.completed",
        extra={"payload": {"task_id": task_id, "status": result.status}},
    )
    return result

@router.post("/agents/requests")
async def create_agent_request(request_data: AgentRequestCreate):
    """Create an inter-team agent request.

    Args:
        request_data: Request payload.

    Returns:
        AgentRequest: Created request.

    Raises:
        None: No explicit exceptions are raised.
    """
    req = AgentRequest(**request_data.model_dump())
    await db.agent_requests.insert_one(req.model_dump())
    logger.info(
        "agent.request.created",
        extra={"payload": {"request_id": req.request_id, "from": req.from_team, "to": req.to_team}},
    )
    return req

@router.get("/agents/requests")
async def list_agent_requests(team_id: str | None = None, status_filter: str | None = None):
    """List agent requests.

    Args:
        team_id: Optional team identifier.
        status_filter: Optional status filter.

    Returns:
        list[dict]: Agent requests.

    Raises:
        None: No explicit exceptions are raised.
    """
    query = {}
    if team_id:
        query["$or"] = [{"from_team": team_id}, {"to_team": team_id}]
    if status_filter:
        query["status"] = status_filter
    requests = await db.agent_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return requests

@router.post("/agents/requests/{request_id}/respond")
async def respond_agent_request(request_id: str, decision: AgentRequestDecision):
    """Respond to an agent request.

    Args:
        request_id: Request identifier.
        decision: Decision payload.

    Returns:
        dict: Updated request.

    Raises:
        HTTPException: If the request does not exist.
    """
    request_doc = await db.agent_requests.find_one({"request_id": request_id}, {"_id": 0})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Request not found")
    updated = {
        "status": decision.status,
        "response": decision.response,
        "responded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.agent_requests.update_one({"request_id": request_id}, {"$set": updated})
    request_doc.update(updated)
    logger.info(
        "agent.request.responded",
        extra={"payload": {"request_id": request_id, "status": decision.status}},
    )
    return request_doc
