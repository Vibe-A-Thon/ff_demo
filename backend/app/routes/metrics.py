"""Metrics API routes.

Provides aggregated dashboard metrics for runs, rules, and telemetry.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.db import db
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/metrics/dashboard")
async def get_dashboard_metrics(current_user: dict = Depends(require_permission("metrics:read"))):
    """Return summary metrics for the dashboard."""
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

    def _coerce_float(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        return None

    run_events_by_run: Dict[str, list[Dict[str, Any]]] = {}
    for event in run_events:
        run_id = event.get("run_id")
        if not run_id:
            continue
        run_events_by_run.setdefault(run_id, []).append(event)

    run_telemetry: Dict[str, Dict[str, Any]] = {}
    for run_id, events in run_events_by_run.items():
        actions_total = 0
        actions_blocked = 0
        actions_review = 0
        actions_allowed = 0
        decisions: list[str] = []
        score_values: list[float] = []

        for event in events:
            if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
                continue
            outputs = (event.get("payload") or {}).get("outputs") or {}
            respond = outputs.get("respond_actions") or outputs.get("respond") or {}
            actions = respond.get("actions") or []
            if isinstance(actions, list):
                for action in actions:
                    action_type = action.get("action")
                    actions_total += 1
                    if action_type == "block":
                        actions_blocked += 1
                    elif action_type == "review":
                        actions_review += 1
                    elif action_type in {"allow", "monitor"}:
                        actions_allowed += 1
            decision = respond.get("decision")
            if isinstance(decision, str):
                decisions.append(decision)

            scored = outputs.get("score_risk") or {}
            avg_score = _coerce_float(scored.get("avg_score"))
            if avg_score is not None:
                score_values.append(avg_score)

        avg_score = sum(score_values) / len(score_values) if score_values else None
        decision = decisions[-1] if decisions else None
        success_rate = (actions_blocked / actions_total * 100) if actions_total else 0
        run_telemetry[run_id] = {
            "actions_total": actions_total,
            "actions_blocked": actions_blocked,
            "actions_review": actions_review,
            "actions_allowed": actions_allowed,
            "decision": decision,
            "avg_score": avg_score,
            "success_rate": success_rate,
        }

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

    decisions = [
        run_telemetry.get(r.get("id"), {}).get("decision") or r.get("last_metrics", {}).get("decision")
        for r in runs
    ]
    decision_counts = {}
    for decision in decisions:
        if decision:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

    avg_risk_score = 0
    scores = []
    for run in runs:
        telemetry_score = run_telemetry.get(run.get("id"), {}).get("avg_score")
        if telemetry_score is not None:
            scores.append(telemetry_score)
            continue
        fallback_score = run.get("last_metrics", {}).get("avg_score")
        if isinstance(fallback_score, (int, float)):
            scores.append(float(fallback_score))
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
        telemetry = run_telemetry.get(run.get("id"), {})
        success_rate = telemetry.get("success_rate")
        if success_rate is not None:
            success_rate_values.append(success_rate)
        time_to_immunity_values.append(run.get("step_count", 0) or 0)
        patterns_values.append(artifacts_by_run.get(run.get("id", ""), 0))

    avg_success = sum(success_rate_values) / len(success_rate_values) if success_rate_values else 0
    avg_time_to_immunity = sum(time_to_immunity_values) / len(time_to_immunity_values) if time_to_immunity_values else 0
    patterns_learned = sum(patterns_values)

    time_series_runs = sorted(completed_runs, key=lambda item: item.get("started_at") or "")[-20:]
    time_series = []
    for run in time_series_runs:
        telemetry = run_telemetry.get(run.get("id"), {})
        success_rate = telemetry.get("success_rate") or 0
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
            "actions_total": sum(item.get("actions_total", 0) for item in run_telemetry.values()),
            "actions_blocked": sum(item.get("actions_blocked", 0) for item in run_telemetry.values()),
            "actions_review": sum(item.get("actions_review", 0) for item in run_telemetry.values()),
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


@router.get("/metrics/perf")
async def get_performance_metrics(current_user: dict = Depends(require_permission("metrics:read"))):
    """Return performance profiling metrics for RAG and graph queries."""
    rag_perf = await db.rag_query_perf.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    graph_perf = await db.graph_query_perf.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)

    def _avg(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    rag_total = [float(item.get("timing", {}).get("total_ms", 0)) for item in rag_perf if item.get("timing")]
    rag_graph = [float(item.get("timing", {}).get("graph_ms", 0)) for item in rag_perf if item.get("timing")]
    rag_cache_hits = len([item for item in rag_perf if item.get("cache_layer") not in {None, "none"}])
    rag_count = len(rag_perf)

    graph_total = [float(item.get("duration_ms", 0)) for item in graph_perf]
    graph_cache_hits = len([item for item in graph_perf if item.get("cache_hit")])
    graph_count = len(graph_perf)

    payload: Dict[str, Any] = {
        "rag": {
            "samples": rag_count,
            "avg_total_ms": round(_avg(rag_total), 2),
            "avg_graph_ms": round(_avg(rag_graph), 2),
            "cache_hit_rate": round((rag_cache_hits / rag_count) if rag_count else 0, 4),
        },
        "graph": {
            "samples": graph_count,
            "avg_total_ms": round(_avg(graph_total), 2),
            "cache_hit_rate": round((graph_cache_hits / graph_count) if graph_count else 0, 4),
        },
    }
    await record_audit(
        current_user.get("id", "unknown"),
        "metrics.perf.generated",
        "metrics",
        "perf",
        metadata={"rag_samples": rag_count, "graph_samples": graph_count},
    )
    return payload

@router.get("/metrics/agent-effectiveness")
async def get_agent_effectiveness(current_user: dict = Depends(require_permission("metrics:read"))):
    """Return effectiveness metrics per agent."""
    tasks = await db.agent_tasks.find({}, {"_id": 0, "target_agent_id": 1, "status": 1, "outcome": 1}).to_list(10000)
    memories = await db.agent_memories.find({}, {"_id": 0, "agent_id": 1}).to_list(10000)

    agent_stats = {}

    for t in tasks:
        aid = t.get("target_agent_id")
        if not aid:
            continue
        if aid not in agent_stats:
            agent_stats[aid] = {"tasks": 0, "success": 0, "memories": 0}
        agent_stats[aid]["tasks"] += 1
        if t.get("status") == "completed":
            agent_stats[aid]["success"] += 1

    for m in memories:
        aid = m.get("agent_id")
        if not aid:
            continue
        if aid not in agent_stats:
            agent_stats[aid] = {"tasks": 0, "success": 0, "memories": 0}
        agent_stats[aid]["memories"] += 1

    payload = []
    for aid, stats in agent_stats.items():
        rate = (stats["success"] / stats["tasks"] * 100) if stats["tasks"] else 0
        payload.append({
            "agent_id": aid,
            "tasks_total": stats["tasks"],
            "success_rate": round(rate, 1),
            "memories_created": stats["memories"]
        })

    return sorted(payload, key=lambda x: x["tasks_total"], reverse=True)


@router.get("/metrics/historical")
async def get_historical_metrics(
    days: int = 30,
    granularity: str = "daily",
    current_user: dict = Depends(require_permission("metrics:read")),
):
    """Get historical time-series metrics from MongoDB aggregations.

    Args:
        days: Number of days to include (default: 30)
        granularity: Time bucket size - 'hourly', 'daily', or 'weekly' (default: 'daily')
        current_user: Authenticated user

    Returns:
        Time-series data with aggregated metrics
    """
    from app.services.metrics.historical_aggregator import HistoricalMetricsAggregator

    aggregator = HistoricalMetricsAggregator(db)
    time_series = await aggregator.get_time_series_metrics(days=days, granularity=granularity)

    logger.info(
        "metrics.historical.generated",
        extra={
            "payload": {
                "days": days,
                "granularity": granularity,
                "data_points": len(time_series),
            }
        },
    )

    await record_audit(
        current_user.get("id", "unknown"),
        "metrics.historical.generated",
        "metrics",
        "historical",
        metadata={"days": days, "granularity": granularity, "data_points": len(time_series)},
    )

    return {
        "period_days": days,
        "granularity": granularity,
        "data_points": len(time_series),
        "time_series": time_series,
    }


@router.get("/metrics/dashboard/v2")
async def get_dashboard_metrics_v2(
    days: int = 30,
    current_user: dict = Depends(require_permission("metrics:read")),
):
    """Get enhanced dashboard metrics with historical aggregations.

    This endpoint replaces /metrics/dashboard with true historical data
    instead of fallback computations.

    Args:
        days: Number of days to aggregate (default: 30)
        current_user: Authenticated user

    Returns:
        Complete dashboard metrics with time-series data
    """
    from app.services.metrics.historical_aggregator import HistoricalMetricsAggregator

    aggregator = HistoricalMetricsAggregator(db)

    # Get aggregated metrics
    metrics = await aggregator.get_aggregated_dashboard_metrics(days=days)

    # Get trend analysis
    trends = await aggregator.get_trend_analysis(days=days)

    # Get current rules count
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)

    # Combine into payload
    payload = {
        "total_battles": metrics["total_battles"],
        "completed_battles": metrics["completed_battles"],
        "running_battles": 0,  # Real-time data from current state
        "avg_success_rate": metrics["avg_success_rate"],
        "total_rules": len(rules),
        "active_rules": len([r for r in rules if r.get("status") == "active"]),
        "patterns_learned": metrics["patterns_learned"],
        "avg_time_to_immunity": metrics["avg_time_to_immunity"],
        "time_series": metrics["time_series"],
        "trends": trends,
        "operational_kpis": {
            "total_runs": metrics["total_battles"],
            "completed_runs": metrics["completed_battles"],
            "total_actions": metrics["total_actions"],
            "blocked_actions": metrics["blocked_actions"],
            "block_rate": metrics["block_rate"],
            "period_days": days,
        },
    }

    logger.info(
        "metrics.dashboard.v2.generated",
        extra={
            "payload": {
                "total_battles": payload["total_battles"],
                "period_days": days,
            }
        },
    )

    await record_audit(
        current_user.get("id", "unknown"),
        "metrics.dashboard.v2.generated",
        "metrics",
        "dashboard_v2",
        metadata={"total_battles": payload["total_battles"], "period_days": days},
    )

    return payload


@router.get("/metrics/trends")
async def get_trend_analysis(
    days: int = 30,
    current_user: dict = Depends(require_permission("metrics:read")),
):
    """Get trend analysis for key metrics.

    Args:
        days: Number of days to analyze (default: 30)
        current_user: Authenticated user

    Returns:
        Trend analysis with percentage changes
    """
    from app.services.metrics.historical_aggregator import HistoricalMetricsAggregator

    aggregator = HistoricalMetricsAggregator(db)
    trends = await aggregator.get_trend_analysis(days=days)

    logger.info(
        "metrics.trends.generated",
        extra={"payload": {"days": days}},
    )

    await record_audit(
        current_user.get("id", "unknown"),
        "metrics.trends.generated",
        "metrics",
        "trends",
        metadata={"days": days},
    )

    return {
        "period_days": days,
        "trends": trends,
    }
