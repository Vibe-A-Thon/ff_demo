"""Audit helpers for LLM events."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.audit import record_audit


async def record_llm_event(
    action: str,
    actor_id: str,
    model_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    version_pin: Optional[str] = None,
    run_id: Optional[str] = None,
    turn_id: Optional[str] = None,
    team_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    payload = dict(metadata or {})
    payload.update(
        {
            "provider": provider,
            "model_name": model_name,
            "version_pin": version_pin,
            "run_id": run_id,
            "turn_id": turn_id,
            "team_id": team_id,
            "agent_id": agent_id,
            "trace_id": trace_id,
        }
    )
    await record_audit(
        actor_id=actor_id or "system",
        action=action,
        target_type="llm",
        target_id=model_id,
        metadata=payload,
    )
