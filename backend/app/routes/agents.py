"""Agent registry and task routes."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.agent_registry import AgentRegistry
from app.agents import get_agent_runtime, orchestrate_multi_team_tasks
from app.models import (
    AgentProfile,
    AgentProfileCreate,
    AgentRequest,
    AgentRequestCreate,
    AgentRequestDecision,
    AgentResult,
    AgentTask,
    AgentArtifact,
    AgentRouteRequest,
    AgentOrchestrationRequest,
)
from app.rag_utils import contains_sensitive_identifiers
from app.teams_data import default_agent_payloads
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)
DEFAULT_REGISTRY = AgentRegistry.from_defaults()


async def _execute_task_with_runtime(task: AgentTask) -> AgentResult:
    runtime = get_agent_runtime(task.target_agent_id or "")
    if not runtime:
        raise HTTPException(status_code=404, detail="Agent runtime not found")
    result = await runtime.run_task(task)
    if result.outputs:
        artifacts = [AgentArtifact(**output).model_dump() for output in result.outputs]
        await db.agent_artifacts.insert_many(artifacts)
    await db.agent_tasks.update_one(
        {"task_id": task.task_id},
        {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return result


def _build_task_payload(
    run_id: str,
    team_id: str,
    agent_id: str,
    task_type: str,
    objective: str,
    inputs: List[Dict[str, Any]],
    params: Dict[str, Any],
    seed: int | None,
) -> AgentTask:
    payload = {
        "run_id": run_id,
        "team_id": team_id,
        "target_agent_id": agent_id,
        "task_type": task_type,
        "inputs": inputs,
        "params": {**params, "objective": objective},
        "seed": seed,
        "created_by": "system",
        "status": "pending",
    }
    return AgentTask(**payload)

@router.get("/agents")
async def list_agents(team_id: str | None = None, current_user: dict = Depends(require_permission("agents:read"))):
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
        await record_audit(
            current_user.get("id", "unknown"),
            "agents.list",
            "agent",
            team_id or "all",
        )
        return agents
    fallback = [agent.model_dump() for agent in DEFAULT_REGISTRY.list_agents(team_id)]
    await record_audit(
        current_user.get("id", "unknown"),
        "agents.list",
        "agent",
        team_id or "all",
    )
    return fallback

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, current_user: dict = Depends(require_permission("agents:read"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agents.read",
        "agent",
        agent_id,
    )
    return agent

@router.get("/agents/registry")
async def get_registry_snapshot(team_id: str | None = None, current_user: dict = Depends(require_permission("agents:read"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agents.registry.snapshot",
        "agent_registry",
        team_id or "all",
    )
    return {"teams": teams, "agents": agents, "delegation_preview": delegation_preview}

@router.post("/agents/register")
async def register_agent(agent_data: AgentProfileCreate, current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agents.registered",
        "agent",
        profile.agent_id,
        metadata={"team_id": profile.team_id},
    )
    logger.info("agent.registered", extra={"payload": {"agent_id": profile.agent_id, "team_id": profile.team_id}})
    return profile

@router.post("/agents/seed")
async def seed_agents(current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agents.seeded",
        "agent",
        "seed",
        metadata={"inserted": inserted, "total": total},
    )
    logger.info("agents.seeded", extra={"payload": {"inserted": inserted, "total": total}})
    return {"message": "Agents seeded", "count": total, "inserted": inserted}

@router.post("/agents/tasks")
async def create_agent_task(task_data: AgentTask, current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.task.created",
        "agent_task",
        task_data.task_id,
        metadata={"team_id": task_data.team_id, "run_id": task_data.run_id},
    )
    logger.info(
        "agent.task.created",
        extra={"payload": {"task_id": task_data.task_id, "team_id": task_data.team_id, "run_id": task_data.run_id}},
    )
    return task_data

@router.get("/agents/tasks")
async def list_agent_tasks(run_id: str | None = None, team_id: str | None = None, status_filter: str | None = None, current_user: dict = Depends(require_permission("agents:read"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.task.list",
        "agent_task",
        run_id or team_id or "all",
        metadata={"run_id": run_id, "team_id": team_id, "status": status_filter},
    )
    return tasks

@router.post("/agents/tasks/{task_id}/complete")
async def complete_agent_task(task_id: str, result: AgentResult, current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.task.completed",
        "agent_task",
        task_id,
        metadata={"status": result.status},
    )
    logger.info(
        "agent.task.completed",
        extra={"payload": {"task_id": task_id, "status": result.status}},
    )
    return result


@router.post("/agents/tasks/{task_id}/execute")
async def execute_agent_task(task_id: str, current_user: dict = Depends(require_permission("agents:write"))):
    """Execute an agent task with deterministic runtime.

    Args:
        task_id: Task identifier.

    Returns:
        AgentResult: Persisted result.

    Raises:
        HTTPException: If the task or agent runtime does not exist.
    """
    task_doc = await db.agent_tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")

    task = AgentTask(**task_doc)
    agent_id = task.target_agent_id
    if not agent_id:
        team_agents = DEFAULT_REGISTRY.list_agents(task.team_id)
        if not team_agents:
            raise HTTPException(status_code=400, detail="No agents available for team")
        agent_id = team_agents[0].agent_id

    task = AgentTask(**{**task.model_dump(), "target_agent_id": agent_id})
    result = await _execute_task_with_runtime(task)
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.task.executed",
        "agent_task",
        task_id,
        metadata={"status": result.status, "agent_id": agent_id},
    )
    logger.info(
        "agent.task.executed",
        extra={"payload": {"task_id": task_id, "status": result.status, "agent_id": agent_id}},
    )
    return result


@router.post("/agents/route")
async def route_agent_tasks(route: AgentRouteRequest, current_user: dict = Depends(require_permission("agents:write"))):
    """Route tasks to multiple agents within a team.

    Args:
        route: Routing payload.

    Returns:
        dict: Routed tasks and optional results.

    Raises:
        HTTPException: If validation fails.
    """
    if route.inputs:
        joined = __import__("json").dumps(route.inputs, default=str)
        if contains_sensitive_identifiers(joined):
            raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    delegation = DEFAULT_REGISTRY.build_delegation_plan(route.team_id, route.objective, max_agents=route.max_agents)
    if not delegation:
        raise HTTPException(status_code=404, detail="No agents available for team")

    tasks: List[AgentTask] = []
    results: List[AgentResult] = []
    for delegate in delegation:
        task = _build_task_payload(
            route.run_id,
            route.team_id,
            delegate["agent_id"],
            route.task_type,
            route.objective,
            route.inputs,
            route.params,
            route.seed,
        )
        await db.agent_tasks.insert_one(task.model_dump())
        tasks.append(task)

        if route.auto_execute:
            result = await _execute_task_with_runtime(task)
            results.append(result)

    await record_audit(
        current_user.get("id", "unknown"),
        "agent.task.routed",
        "agent_task",
        route.team_id,
        metadata={"run_id": route.run_id, "count": len(tasks), "auto_execute": route.auto_execute},
    )
    logger.info(
        "agent.task.routed",
        extra={"payload": {"team_id": route.team_id, "run_id": route.run_id, "count": len(tasks)}},
    )
    return {"tasks": [task.model_dump() for task in tasks], "results": [r.model_dump() for r in results]}


@router.post("/agents/orchestrate")
async def orchestrate_team_tasks(payload: AgentOrchestrationRequest, current_user: dict = Depends(require_permission("agents:write"))):
    """Orchestrate tasks across multiple teams.

    Args:
        payload: Orchestration payload.

    Returns:
        dict: Orchestration result.

    Raises:
        HTTPException: If validation fails.
    """
    if payload.inputs:
        joined = __import__("json").dumps(payload.inputs, default=str)
        if contains_sensitive_identifiers(joined):
            raise HTTPException(status_code=400, detail="Synthetic-only mode: sensitive identifiers detected")

    orchestrated = await orchestrate_multi_team_tasks(
        payload.run_id,
        payload.objective,
        payload.teams,
        payload.task_type,
        payload.inputs,
        payload.params,
        payload.max_agents_per_team,
        payload.auto_execute,
        payload.seed,
    )

    orchestrated_tasks: List[Dict[str, Any]] = []
    all_results: List[Dict[str, Any]] = []
    for bundle in orchestrated["teams"]:
        team_tasks = bundle["tasks"]
        for task in team_tasks:
            await db.agent_tasks.insert_one(task.model_dump())
        orchestrated_tasks.append(
            {"team_id": bundle["team_id"], "tasks": [task.model_dump() for task in team_tasks]}
        )
        for execution in bundle["executions"]:
            task = execution["task"]
            result = execution["result"]
            if result.outputs:
                artifacts = [AgentArtifact(**output).model_dump() for output in result.outputs]
                await db.agent_artifacts.insert_many(artifacts)
            await db.agent_tasks.update_one(
                {"task_id": task.task_id},
                {"$set": {"status": result.status, "result": result.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
            )
            all_results.append(result.model_dump())

    await record_audit(
        current_user.get("id", "unknown"),
        "agent.orchestrated",
        "agent_task",
        payload.run_id,
        metadata={"teams": payload.teams, "auto_execute": payload.auto_execute},
    )
    logger.info(
        "agent.orchestrated",
        extra={"payload": {"run_id": payload.run_id, "teams": payload.teams}},
    )
    return {"tasks": orchestrated_tasks, "results": all_results, "lineage": orchestrated["lineage"]}


@router.get("/agents/artifacts")
async def list_agent_artifacts(
    run_id: str | None = None,
    task_id: str | None = None,
    agent_id: str | None = None,
    artifact_type: str | None = None,
    current_user: dict = Depends(require_permission("agents:read")),
):
    """List agent artifacts.

    Args:
        run_id: Optional run identifier.
        task_id: Optional task identifier.
        agent_id: Optional agent identifier.
        artifact_type: Optional artifact type.

    Returns:
        list[dict]: Agent artifacts.
    """
    query: Dict[str, Any] = {}
    if run_id:
        query["run_id"] = run_id
    if task_id:
        query["task_id"] = task_id
    if agent_id:
        query["agent_id"] = agent_id
    if artifact_type:
        query["artifact_type"] = artifact_type
    artifacts = await db.agent_artifacts.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.artifacts.list",
        "agent_artifact",
        run_id or agent_id or "all",
        metadata={"run_id": run_id, "task_id": task_id, "agent_id": agent_id, "artifact_type": artifact_type},
    )
    return artifacts


@router.get("/agents/artifacts/{artifact_id}")
async def get_agent_artifact(artifact_id: str, current_user: dict = Depends(require_permission("agents:read"))):
    """Get a single agent artifact.

    Args:
        artifact_id: Artifact identifier.

    Returns:
        dict: Agent artifact.
    """
    artifact = await db.agent_artifacts.find_one({"artifact_id": artifact_id}, {"_id": 0})
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.artifact.read",
        "agent_artifact",
        artifact_id,
    )
    return artifact


@router.get("/agents/artifacts/{artifact_id}/lineage")
async def get_agent_artifact_lineage(artifact_id: str, current_user: dict = Depends(require_permission("agents:read"))):
    """Get lineage for a specific artifact.

    Args:
        artifact_id: Artifact identifier.

    Returns:
        dict: Lineage details.
    """
    artifact = await db.agent_artifacts.find_one({"artifact_id": artifact_id}, {"_id": 0})
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    lineage_inputs = artifact.get("lineage", {}).get("inputs", [])
    parent_ids = [item.get("artifact_id") for item in lineage_inputs if isinstance(item, dict) and item.get("artifact_id")]
    parents = []
    if parent_ids:
        parents = await db.agent_artifacts.find({"artifact_id": {"$in": parent_ids}}, {"_id": 0}).to_list(200)

    children = await db.agent_artifacts.find({"lineage.inputs.artifact_id": artifact_id}, {"_id": 0}).to_list(200)

    await record_audit(
        current_user.get("id", "unknown"),
        "agent.artifact.lineage",
        "agent_artifact",
        artifact_id,
    )
    return {"artifact": artifact, "parents": parents, "children": children}

@router.post("/agents/requests")
async def create_agent_request(request_data: AgentRequestCreate, current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.request.created",
        "agent_request",
        req.request_id,
        metadata={"from_team": req.from_team, "to_team": req.to_team},
    )
    logger.info(
        "agent.request.created",
        extra={"payload": {"request_id": req.request_id, "from": req.from_team, "to": req.to_team}},
    )
    return req

@router.get("/agents/requests")
async def list_agent_requests(team_id: str | None = None, status_filter: str | None = None, current_user: dict = Depends(require_permission("agents:read"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.request.list",
        "agent_request",
        team_id or "all",
        metadata={"team_id": team_id, "status": status_filter},
    )
    return requests

@router.post("/agents/requests/{request_id}/respond")
async def respond_agent_request(request_id: str, decision: AgentRequestDecision, current_user: dict = Depends(require_permission("agents:write"))):
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
    await record_audit(
        current_user.get("id", "unknown"),
        "agent.request.responded",
        "agent_request",
        request_id,
        decision=decision.status,
        metadata={"reason": decision.response},
    )
    logger.info(
        "agent.request.responded",
        extra={"payload": {"request_id": request_id, "status": decision.status}},
    )
    return request_doc
