from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import RunSession, RunStartRequest
from app.run_helpers import record_run_event
from app.tooling import derive_seed
from app.workflow_service import (
    WAR_LOOP_STAGES,
    next_war_loop_stage,
    execute_war_loop_stage,
    stage_is_approved,
    ensure_stage_approval,
)

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

    current_stage = run.get("current_stage") or "init"
    if current_stage == "init":
        current_stage = WAR_LOOP_STAGES[0]

    if current_stage == "done":
        return {"run_id": run_id, "status": "completed"}

    step_index = int(run.get("step_count", 0)) + 1
    base_seed = int(run.get("seed", int(datetime.now(timezone.utc).timestamp())))
    step_seed = derive_seed(base_seed, f"{current_stage}-{step_index}")

    if current_stage in {"orange_review_approve", "white_compliance_audit"}:
        approved = await stage_is_approved(run_id, current_stage)
        if not approved:
            approval = await ensure_stage_approval(run_id, current_stage, requestor_id="system")
            await record_run_event(
                run_id,
                "stage.pending_approval",
                {"stage": current_stage, "step": step_index, "approval_id": (approval or {}).get("id")},
            )
            await db.runs.update_one(
                {"id": run_id},
                {
                    "$set": {
                        "current_stage": current_stage,
                        "status": "awaiting_approval",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )
            return {"run_id": run_id, "stage": current_stage, "status": "awaiting_approval"}

    await record_run_event(run_id, "stage.changed", {"stage": current_stage, "step": step_index})
    stage_payload, next_override = await execute_war_loop_stage(run, current_stage, step_seed)

    if stage_payload.get("agent"):
        agent_info = stage_payload["agent"]
        await record_run_event(
            run_id,
            "agent.output",
            {"agent": agent_info.get("agent_id"), "team": agent_info.get("team_id"), "outputs": stage_payload.get("outputs")},
        )

    update_fields = {
        "current_stage": current_stage,
        "step_count": step_index,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
    }

    if current_stage == "red_simulate_attack":
        outputs = stage_payload.get("outputs", {})
        simulated = outputs.get("simulate_transactions", {})
        attacked = outputs.get("apply_attack", {})
        events = attacked.get("attacked_events") or simulated.get("events") or []
        update_fields["last_events"] = events
    elif current_stage == "blue_detect_respond":
        outputs = stage_payload.get("outputs", {})
        scored = outputs.get("score_risk", {})
        response = outputs.get("respond_actions", {})
        decision = response.get("decision", "monitor")
        update_fields["last_decision"] = decision
        update_fields["last_metrics"] = {
            "avg_score": scored.get("avg_score", 0),
            "decision": decision,
            "actions": len(response.get("actions", [])),
        }

    if next_override:
        await record_run_event(run_id, "stage.failed", {"stage": current_stage, "next": next_override, "step": step_index})
        update_fields["current_stage"] = next_override
        await db.runs.update_one({"id": run_id}, {"$set": update_fields})
        return {
            "run_id": run_id,
            "stage": current_stage,
            "status": "failed",
            "loop_back": next_override,
            "payload": stage_payload,
        }

    next_stage = next_war_loop_stage(current_stage)
    update_fields["current_stage"] = next_stage
    if next_stage == "done":
        update_fields["status"] = "completed"

    await db.runs.update_one({"id": run_id}, {"$set": update_fields})
    return {
        "run_id": run_id,
        "stage": current_stage,
        "next_stage": next_stage,
        "payload": stage_payload,
        "metrics": update_fields.get("last_metrics"),
    }
