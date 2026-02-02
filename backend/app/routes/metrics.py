"""Metrics API routes.

Provides aggregated dashboard metrics for runs, rules, and telemetry.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.db import db
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/metrics/dashboard")
async def get_dashboard_metrics(current_user: dict = Depends(require_permission("metrics:read"))):
    """Return summary metrics for the dashboard.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        dict: Aggregated metrics for battles and rules.

    Raises:
        None: No explicit exceptions are raised.
    """
    runs = await db.runs.find({}, {"_id": 0}).to_list(200)
    run_events = await db.run_events.find({}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    artifacts = await db.agent_artifacts.find({}, {"_id": 0, "run_id": 1}).to_list(2000)
    tasks = await db.agent_tasks.find({}, {"_id": 0, "status": 1}).to_list(2000)
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)

    run_status_counts = {
        "completed": len([r for r in runs if r.get("status") == "completed"]),
        "running": len([r for r in runs if r.get("status") == "running"]),
        "awaiting_approval": len([r for r in runs if r.get("status") == "awaiting_approval"]),
    }
    total_runs = len(runs)

    def _parse_ts(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    stage_events_by_run: dict[str, list[dict]] = {}
    stage_failures = 0
    stage_changes = 0
    for event in run_events:
        if event.get("event_type") == "stage.changed":
            stage_changes += 1
            stage_events_by_run.setdefault(event.get("run_id", ""), []).append(event)
        if event.get("event_type") == "stage.failed":
            stage_failures += 1

    stage_durations = []
    for run_id, events in stage_events_by_run.items():
        sorted_events = sorted(events, key=lambda item: item.get("created_at") or "")
        for prev, curr in zip(sorted_events, sorted_events[1:]):
            prev_ts = _parse_ts(prev.get("created_at"))
            curr_ts = _parse_ts(curr.get("created_at"))
            if prev_ts and curr_ts:
                stage_durations.append((curr_ts - prev_ts).total_seconds())

    avg_stage_duration = sum(stage_durations) / len(stage_durations) if stage_durations else 0
    stage_failure_rate = (stage_failures / stage_changes) if stage_changes else 0

    decisions = [r.get("last_metrics", {}).get("decision") for r in runs if r.get("last_metrics")]
    decision_counts = {}
    for decision in decisions:
        if decision:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

    avg_risk_score = 0
    scores = [r.get("last_metrics", {}).get("avg_score", 0) for r in runs if r.get("last_metrics")]
    if scores:
        avg_risk_score = sum(scores) / len(scores)

    artifacts_by_run = {}
    for artifact in artifacts:
        run_id = artifact.get("run_id")
        if run_id:
            artifacts_by_run[run_id] = artifacts_by_run.get(run_id, 0) + 1

    completed_runs = [r for r in runs if r.get("status") == "completed"]
    success_rate_values = []
    time_to_immunity_values = []
    patterns_values = []
    for run in completed_runs:
        decision = run.get("last_metrics", {}).get("decision")
        if decision == "block":
            success_rate_values.append(100)
        elif decision == "review":
            success_rate_values.append(60)
        elif decision == "monitor":
            success_rate_values.append(40)
        elif decision:
            success_rate_values.append(50)
        time_to_immunity_values.append(run.get("step_count", 0) or 0)
        patterns_values.append(artifacts_by_run.get(run.get("id", ""), 0))

    avg_success = sum(success_rate_values) / len(success_rate_values) if success_rate_values else 0
    avg_time_to_immunity = sum(time_to_immunity_values) / len(time_to_immunity_values) if time_to_immunity_values else 0
    patterns_learned = sum(patterns_values)

    time_series_runs = sorted(completed_runs, key=lambda item: item.get("started_at") or "")[-20:]
    time_series = []
    for run in time_series_runs:
        decision = run.get("last_metrics", {}).get("decision")
        success_rate = 50
        if decision == "block":
            success_rate = 100
        elif decision == "review":
            success_rate = 60
        elif decision == "monitor":
            success_rate = 40
        time_series.append(
            {
                "timestamp": run.get("started_at"),
                "success_rate": success_rate,
                "time_to_immunity": run.get("step_count", 0) or 0,
                "patterns_learned": artifacts_by_run.get(run.get("id", ""), 0),
            }
        )

    payload = {
        "total_battles": total_runs,
        "completed_battles": run_status_counts["completed"],
        "running_battles": run_status_counts["running"],
        "avg_success_rate": round(avg_success, 2),
        "total_rules": len(rules),
        "active_rules": len([r for r in rules if r.get("status") == "active"]),
        "patterns_learned": patterns_learned,
        "avg_time_to_immunity": round(avg_time_to_immunity, 2),
        "time_series": time_series,
        "operational_kpis": {
            "total_runs": total_runs,
            "completed_runs": run_status_counts["completed"],
            "running_runs": run_status_counts["running"],
            "awaiting_approval_runs": run_status_counts["awaiting_approval"],
            "avg_stage_duration_sec": round(avg_stage_duration, 2),
            "stage_failure_rate": round(stage_failure_rate, 4),
            "avg_risk_score": round(avg_risk_score, 2),
            "decision_counts": decision_counts,
            "artifacts_total": len(artifacts),
            "tasks_total": len(tasks),
            "tasks_completed": len([t for t in tasks if t.get("status") == "completed"]),
        },
    }
    logger.info(
        "metrics.dashboard.generated",
        extra={"payload": {"total_runs": payload["operational_kpis"]["total_runs"], "total_rules": payload["total_rules"]}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "metrics.dashboard.generated",
        "metrics",
        "dashboard",
        metadata={"total_runs": payload["operational_kpis"]["total_runs"], "total_rules": payload["total_rules"]},
    )
    return payload
