"""LLM telemetry recording helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.db import db


async def record_llm_telemetry_event(
    *,
    action: str,
    model_id: str,
    provider: str,
    model_name: str | None = None,
    run_id: str | None = None,
    turn_id: str | None = None,
    team_id: str | None = None,
    agent_id: str | None = None,
    trace_id: str | None = None,
    latency_ms: float | None = None,
    schema_valid: bool | None = None,
    repair_used: bool = False,
    fallback_used: bool = False,
    error: str | None = None,
) -> None:
    payload = {
        "action": action,
        "model_id": model_id,
        "provider": provider,
        "model_name": model_name,
        "run_id": run_id,
        "turn_id": turn_id,
        "team_id": team_id,
        "agent_id": agent_id,
        "trace_id": trace_id,
        "latency_ms": latency_ms,
        "schema_valid": schema_valid,
        "repair_used": repair_used,
        "fallback_used": fallback_used,
        "error": error,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.llm_telemetry_events.insert_one(payload)

    updates: Dict[str, Any] = {
        "$inc": {
            "total_calls": 1,
            "schema_valid": 1 if schema_valid else 0,
            "schema_invalid": 0 if schema_valid else 1,
            "repairs": 1 if repair_used else 0,
            "fallbacks": 1 if fallback_used else 0,
            "errors": 1 if error else 0,
        },
        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
    }
    await db.llm_telemetry.update_one(
        {"model_id": model_id, "provider": provider, "team_id": team_id, "agent_id": agent_id},
        updates,
        upsert=True,
    )
