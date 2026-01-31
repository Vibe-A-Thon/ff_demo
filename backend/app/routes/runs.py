from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.agents import RED_AGENT, BLUE_AGENT, GOLD_AGENT
from app.db import db
from app.models import RunSession, RunStartRequest
from app.run_helpers import record_run_event
from app.tooling import derive_seed

router = APIRouter()

@router.post("/runs/start")
async def start_run(payload: RunStartRequest):
    seed_value = payload.seed if payload.seed is not None else int(datetime.now(timezone.utc).timestamp())
    run = RunSession(scenario_id=payload.scenario_id, seed=seed_value, mode=payload.mode)
    await db.runs.insert_one(run.model_dump())
    await record_run_event(run.id, "run.started", {"scenario_id": run.scenario_id, "seed": run.seed, "mode": run.mode})
    return run

@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return {"run": run, "events": events}

@router.post("/runs/{run_id}/step")
async def step_run(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    step_index = int(run.get("step_count", 0)) + 1
    base_seed = int(run.get("seed", int(datetime.now(timezone.utc).timestamp())))
    step_seed = derive_seed(base_seed, f"step-{step_index}")

    await record_run_event(run_id, "stage.changed", {"stage": "red_simulate", "step": step_index})
    red_trace = await RED_AGENT.emit({"scenario_id": run.get("scenario_id")}, step_seed)
    simulated = red_trace.outputs.get("simulate_transactions", {})
    attacked = red_trace.outputs.get("apply_attack", {})

    events = attacked.get("attacked_events") or simulated.get("events") or []
    await record_run_event(run_id, "agent.output", {"agent": red_trace.agent_id, "team": red_trace.team_id, "outputs": red_trace.outputs})

    await record_run_event(run_id, "stage.changed", {"stage": "blue_detect", "step": step_index})
    blue_trace = await BLUE_AGENT.emit({"events": events}, step_seed)
    scored = blue_trace.outputs.get("score_risk", {})
    response = blue_trace.outputs.get("respond_actions", {})
    await record_run_event(run_id, "agent.output", {"agent": blue_trace.agent_id, "team": blue_trace.team_id, "outputs": blue_trace.outputs})

    decision = response.get("decision", "monitor")
    await record_run_event(run_id, "stage.changed", {"stage": "gold_explain", "step": step_index})
    gold_trace = await GOLD_AGENT.emit({"decision": decision}, step_seed)
    await record_run_event(run_id, "agent.output", {"agent": gold_trace.agent_id, "team": gold_trace.team_id, "outputs": gold_trace.outputs})

    update_fields = {
        "current_stage": "gold_explain",
        "step_count": step_index,
        "last_decision": decision,
        "last_metrics": {
            "avg_score": scored.get("avg_score", 0),
            "decision": decision,
            "actions": len(response.get("actions", [])),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.runs.update_one({"id": run_id}, {"$set": update_fields})
    return {
        "run_id": run_id,
        "step": step_index,
        "red": red_trace.model_dump(),
        "blue": blue_trace.model_dump(),
        "gold": gold_trace.model_dump(),
        "metrics": update_fields["last_metrics"],
    }
