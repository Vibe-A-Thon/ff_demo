"""War loop run routes.

Start, step, and export war loop runs.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
import io
import json
import zipfile
from app.core.external_services import DatabaseClient
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.deps import get_db
from app.models import RunSession, RunStartRequest, RunReplayRequest
from app.run_helpers import record_run_event
from app.tooling import derive_seed
from app.workflow_service import (
    WAR_LOOP_STAGES,
    next_war_loop_stage,
    execute_war_loop_stage,
    stage_is_approved,
    ensure_stage_approval,
)
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)


@router.get("/runs")
async def list_runs(
    current_user: dict = Depends(require_permission("workflow:read")),
    db: DatabaseClient = Depends(get_db),
) -> List[Dict]:
    """List run sessions.

    Args:
        current_user: Authorized user context.
        db: Database client.

    Returns:
        List[Dict]: Run sessions.

    Raises:
        None: No explicit exceptions are raised.
    """
    runs = await db.runs.find({}, {"_id": 0}).sort("started_at", -1).to_list(200)
    await record_audit(
        current_user.get("id", "unknown"),
        "run.list",
        "run",
        "list",
    )
    return runs

@router.post("/runs/start")
async def start_run(
    payload: RunStartRequest,
    current_user: dict = Depends(require_permission("workflow:control")),
    db: DatabaseClient = Depends(get_db),
) -> RunSession:
    """Start a war loop run.

    Args:
        payload: Run start payload.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        RunSession: Created run.

    Raises:
        None: No explicit exceptions are raised.
    """
    seed_value = payload.seed if payload.seed is not None else int(datetime.now(timezone.utc).timestamp())
    run = RunSession(scenario_id=payload.scenario_id, seed=seed_value, mode=payload.mode)
    await db.runs.insert_one(run.model_dump())
    await record_run_event(run.id, "run.started", {"scenario_id": run.scenario_id, "seed": run.seed, "mode": run.mode})
    await record_audit(
        current_user.get("id", "unknown"),
        "run.started",
        "run",
        run.id,
        metadata={"scenario_id": run.scenario_id, "seed": run.seed, "mode": run.mode},
    )
    logger.info(
        "run.created",
        extra={"payload": {"run_id": run.id, "scenario_id": run.scenario_id, "mode": run.mode}},
    )
    return run

@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    current_user: dict = Depends(require_permission("workflow:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Get a run and its events.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Dict[str, Any]: Run and events.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "run.read",
        "run",
        run_id,
        metadata={"stage": run.get("current_stage") or "init"},
    )
    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return {"run": run, "events": events}

@router.post("/runs/{run_id}/step")
async def step_run(
    run_id: str,
    current_user: dict = Depends(require_permission("workflow:control")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Advance the run by one stage.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Dict[str, Any]: Stage result.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    current_stage = run.get("current_stage") or "init"
    if current_stage == "init":
        current_stage = WAR_LOOP_STAGES[0]

    if current_stage == "done":
        await record_audit(
            current_user.get("id", "unknown"),
            "run.step",
            "run",
            run_id,
            decision="completed",
            metadata={"stage": current_stage},
        )
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
            logger.info(
                "run.awaiting_approval",
                extra={"payload": {"run_id": run_id, "stage": current_stage, "step": step_index}},
            )
            await record_audit(
                current_user.get("id", "unknown"),
                "run.step",
                "run",
                run_id,
                decision="awaiting_approval",
                metadata={"stage": current_stage, "step": step_index},
            )
            return {"run_id": run_id, "stage": current_stage, "status": "awaiting_approval"}

    await record_run_event(run_id, "stage.changed", {"stage": current_stage, "step": step_index})
    logger.info(
        "run.stage.started",
        extra={"payload": {"run_id": run_id, "stage": current_stage, "step": step_index}},
    )
    stage_payload, next_override = await execute_war_loop_stage(run, current_stage, step_seed)
    bundle_artifacts = stage_payload.get("bundle", {}).get("artifacts", []) if isinstance(stage_payload, dict) else []

    if stage_payload.get("agent"):
        agent_info = stage_payload["agent"]
        await record_run_event(
            run_id,
            "agent.output",
            {"agent": agent_info.get("agent_id"), "team": agent_info.get("team_id"), "outputs": stage_payload.get("outputs")},
        )
    if stage_payload.get("orchestrator"):
        orchestrator_info = stage_payload["orchestrator"]
        await record_run_event(
            run_id,
            "orchestrator.output",
            {
                "agent": orchestrator_info.get("agent_id"),
                "team": orchestrator_info.get("team_id"),
                "outputs": orchestrator_info.get("outputs"),
            },
        )
    if bundle_artifacts:
        update_fields["stage_inputs"] = [
            {"artifact_id": artifact.get("artifact_id"), "artifact_type": artifact.get("artifact_type")}
            for artifact in bundle_artifacts
        ]

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
        logger.info(
            "run.stage.failed",
            extra={"payload": {"run_id": run_id, "stage": current_stage, "next": next_override, "step": step_index}},
        )
        await record_audit(
            current_user.get("id", "unknown"),
            "run.step",
            "run",
            run_id,
            decision="failed",
            metadata={"stage": current_stage, "next": next_override, "step": step_index},
        )
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
    logger.info(
        "run.stage.completed",
        extra={"payload": {"run_id": run_id, "stage": current_stage, "next_stage": next_stage, "status": update_fields.get("status")}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "run.step",
        "run",
        run_id,
        metadata={"stage": current_stage, "next_stage": next_stage, "status": update_fields.get("status")},
    )
    return {
        "run_id": run_id,
        "stage": current_stage,
        "next_stage": next_stage,
        "payload": stage_payload,
        "metrics": update_fields.get("last_metrics"),
    }


@router.post("/runs/{run_id}/replay")
async def replay_run(
    run_id: str,
    payload: RunReplayRequest,
    current_user: dict = Depends(require_permission("workflow:control")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Replay a run by resetting stage state and optionally clearing events.

    Args:
        run_id: Run identifier.
        payload: Replay payload.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        dict: Replay result.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    seed_value = payload.seed if payload.seed is not None else int(run.get("seed", int(datetime.now(timezone.utc).timestamp())))
    mode_value = payload.mode or run.get("mode", "auto")

    update_fields = {
        "seed": seed_value,
        "mode": mode_value,
        "status": "running",
        "current_stage": "init",
        "step_count": 0,
        "last_events": [],
        "last_decision": None,
        "last_metrics": {},
        "stage_inputs": [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.runs.update_one({"id": run_id}, {"$set": update_fields})

    if payload.reset_events:
        await db.run_events.delete_many({"run_id": run_id})

    if payload.clear_agent_tasks:
        await db.agent_tasks.delete_many({"run_id": run_id})
    if payload.clear_agent_artifacts:
        await db.agent_artifacts.delete_many({"run_id": run_id})

    await record_run_event(run_id, "run.replayed", {"seed": seed_value, "mode": mode_value})
    await record_audit(
        current_user.get("id", "unknown"),
        "run.replayed",
        "run",
        run_id,
        metadata={"seed": seed_value, "mode": mode_value, "reset_events": payload.reset_events},
    )
    logger.info(
        "run.replayed",
        extra={"payload": {"run_id": run_id, "seed": seed_value, "mode": mode_value}},
    )
    return {"run_id": run_id, "seed": seed_value, "mode": mode_value, "status": "replayed"}


@router.get("/runs/{run_id}/export-brc")
async def export_brc(
    run_id: str,
    current_user: dict = Depends(require_permission("workflow:read")),
    db: DatabaseClient = Depends(get_db),
) -> Response:
    """Export a run as a BRC archive.

    Args:
        run_id: Run identifier.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Response: Archive payload.

    Raises:
        HTTPException: If run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    battle_type = run.get("scenario_id", "battle")
    archive_name = f"{battle_type}_{run_id}_{timestamp}.brc"

    red_simulation_payload = None
    for event in events:
        if event.get("event_type") != "agent.output":
            continue
        payload = event.get("payload", {})
        if str(payload.get("team", "")).lower() == "red":
            red_simulation_payload = payload
            break

    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        artifacts = ["manifest.json", "metadata.json"]
        if red_simulation_payload:
            artifacts.append("red_simulation_data.json")
        manifest = {
            "battle_type": battle_type,
            "run_id": run_id,
            "exported_at": timestamp,
            "event_count": len(events),
            "artifacts": artifacts,
        }
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))

        metadata = {
            "battle_type": battle_type,
            "run_id": run_id,
            "seed": run.get("seed"),
            "mode": run.get("mode"),
            "current_stage": run.get("current_stage"),
            "step_count": run.get("step_count"),
            "exported_at": timestamp,
            "schema_version": "1.1",
        }
        archive.writestr("metadata.json", json.dumps(metadata, indent=2, default=str))

        if red_simulation_payload:
            red_outputs = red_simulation_payload.get("outputs", {})
            red_data = {
                "team": red_simulation_payload.get("team"),
                "agent": red_simulation_payload.get("agent"),
                "simulate_transactions": red_outputs.get("simulate_transactions", {}),
                "apply_attack": red_outputs.get("apply_attack", {}),
                "attack_plan": red_outputs.get("attack_plan", {}),
            }
            archive.writestr("red_simulation_data.json", json.dumps(red_data, indent=2, default=str))

        for event in events:
            if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
                continue
            payload = event.get("payload", {})
            team = payload.get("team", "unknown")
            team_name = str(team).title()
            event_ts = event.get("created_at", timestamp)
            safe_ts = event_ts.replace(":", "").replace("-", "").replace(".", "")
            file_name = f"{team_name}_{run_id}_{safe_ts}.json"
            archive.writestr(file_name, json.dumps(payload, indent=2, default=str))

    memory.seek(0)
    headers = {"Content-Disposition": f"attachment; filename={archive_name}"}
    await record_audit(
        current_user.get("id", "unknown"),
        "run.exported",
        "run",
        run_id,
        metadata={"archive": archive_name},
    )
    return Response(content=memory.read(), media_type="application/octet-stream", headers=headers)
