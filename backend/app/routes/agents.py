from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.agent_registry import AgentRegistry
from app.models import AgentProfile, AgentProfileCreate, AgentRequest, AgentRequestCreate, AgentRequestDecision, AgentResult, AgentTask
from app.rag_utils import contains_sensitive_identifiers
from app.teams_data import default_agent_payloads

router = APIRouter()
DEFAULT_REGISTRY = AgentRegistry.from_defaults()

@router.get("/agents")
async def list_agents(team_id: str | None = None):
    query = {}
    if team_id:
        query["team_id"] = team_id
    agents = await db.agents.find(query, {"_id": 0}).to_list(200)
    if agents:
        return agents
    return [agent.model_dump() for agent in DEFAULT_REGISTRY.list_agents(team_id)]

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    agent = await db.agents.find_one({"agent_id": agent_id}, {"_id": 0})
    if not agent:
        fallback = DEFAULT_REGISTRY.get_agent(agent_id)
        if fallback:
            return fallback.model_dump()
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.get("/agents/registry")
async def get_registry_snapshot(team_id: str | None = None):
    teams = [team.model_dump() for team in DEFAULT_REGISTRY.list_teams()]
    agents = [agent.model_dump() for agent in DEFAULT_REGISTRY.list_agents(team_id)]
    preview_team = team_id or (teams[0]["team_id"] if teams else None)
    delegation_preview = (
        DEFAULT_REGISTRY.build_delegation_plan(preview_team, "Registry preview") if preview_team else []
    )
    return {"teams": teams, "agents": agents, "delegation_preview": delegation_preview}

@router.post("/agents/register")
async def register_agent(agent_data: AgentProfileCreate):
    profile = AgentProfile(**agent_data.model_dump())
    await db.agents.insert_one(profile.model_dump())
    return profile

@router.post("/agents/seed")
async def seed_agents():
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
    return {"message": "Agents seeded", "count": total, "inserted": inserted}

@router.post("/agents/tasks")
async def create_agent_task(task_data: AgentTask):
    if task_data.inputs:
        joined = __import__("json").dumps(task_data.inputs, default=str)
        if contains_sensitive_identifiers(joined):
            raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")
    await db.agent_tasks.insert_one(task_data.model_dump())
    return task_data

@router.get("/agents/tasks")
async def list_agent_tasks(run_id: str | None = None, team_id: str | None = None, status_filter: str | None = None):
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
    task = await db.agent_tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.agent_tasks.update_one(
        {"task_id": task_id},
        {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return result

@router.post("/agents/requests")
async def create_agent_request(request_data: AgentRequestCreate):
    req = AgentRequest(**request_data.model_dump())
    await db.agent_requests.insert_one(req.model_dump())
    return req

@router.get("/agents/requests")
async def list_agent_requests(team_id: str | None = None, status_filter: str | None = None):
    query = {}
    if team_id:
        query["$or"] = [{"from_team": team_id}, {"to_team": team_id}]
    if status_filter:
        query["status"] = status_filter
    requests = await db.agent_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return requests

@router.post("/agents/requests/{request_id}/respond")
async def respond_agent_request(request_id: str, decision: AgentRequestDecision):
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
    return request_doc
