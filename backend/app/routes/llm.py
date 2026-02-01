"""LLM configuration and telemetry routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import get_integration_setting
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.deps import get_db
from app.security import require_permission
from app.core.external_services import DatabaseClient
from app.llm.model_registry import load_model_registry
from app.llm.routing_policy import load_routing_policy

router = APIRouter()
logger = get_logger(__name__)


class LLMConfigUpdate(BaseModel):
    global_default: Optional[str] = None
    team_defaults: Dict[str, str] = {}
    agent_defaults: Dict[str, str] = {}
    intent_defaults: Dict[str, str] = {}
    fallback_chains: Dict[str, List[str]] = {}
    simulate_failure: Dict[str, Any] = {}


@router.get("/llm/config")
async def get_llm_config(
    current_user: dict = Depends(require_permission("settings:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    registry = load_model_registry()
    policy = load_routing_policy()
    overrides_record = await db.platform_settings.find_one({"key": "llm_overrides"}, {"_id": 0})
    overrides = overrides_record.get("payload") if overrides_record else {}

    payload = {
        "registry": [spec.__dict__ for spec in registry.values()],
        "policy": {
            "global_default": policy.global_default,
            "team_defaults": policy.team_defaults,
            "agent_defaults": policy.agent_defaults,
            "intent_defaults": policy.intent_defaults,
            "fallback_chains": policy.fallback_chains,
        },
        "overrides": overrides or {},
    }
    await record_audit(
        current_user.get("id", "unknown"),
        "llm.config.read",
        "llm",
        "config",
    )
    return payload


@router.put("/llm/config")
async def update_llm_config(
    config: LLMConfigUpdate,
    current_user: dict = Depends(require_permission("settings:write")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    payload = config.model_dump()
    await db.platform_settings.update_one(
        {"key": "llm_overrides"},
        {"$set": {"key": "llm_overrides", "payload": payload}},
        upsert=True,
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "llm.config.update",
        "llm",
        "config",
        metadata=payload,
    )
    logger.info("llm.config.update", extra={"payload": payload})
    return payload


@router.get("/llm/telemetry")
async def get_llm_telemetry(
    team_id: Optional[str] = None,
    current_user: dict = Depends(require_permission("metrics:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    query: Dict[str, Any] = {}
    if team_id:
        query["team_id"] = team_id

    snapshots = await db.llm_telemetry.find(query, {"_id": 0}).to_list(200)
    events = await db.llm_telemetry_events.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)

    def _p95(values: List[float]) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        index = int(0.95 * (len(sorted_vals) - 1))
        return float(sorted_vals[index])

    latency_map: Dict[str, List[float]] = {}
    for event in events:
        key = event.get("team_id") or "unknown"
        latency = event.get("latency_ms")
        if latency is None:
            continue
        latency_map.setdefault(key, []).append(float(latency))

    team_stats = []
    for snap in snapshots:
        team_key = snap.get("team_id") or "unknown"
        total = snap.get("total_calls", 0) or 0
        schema_valid = snap.get("schema_valid", 0) or 0
        team_stats.append(
            {
                "team_id": team_key,
                "agent_id": snap.get("agent_id"),
                "model_id": snap.get("model_id"),
                "provider": snap.get("provider"),
                "total_calls": total,
                "schema_valid_rate": schema_valid / total if total else 0.0,
                "repairs": snap.get("repairs", 0) or 0,
                "fallbacks": snap.get("fallbacks", 0) or 0,
                "errors": snap.get("errors", 0) or 0,
                "p95_latency_ms": _p95(latency_map.get(team_key, [])),
            }
        )

    return {
        "teams": team_stats,
        "events": events[:200],
    }
