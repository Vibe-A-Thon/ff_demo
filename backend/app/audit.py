import json
import hashlib
from typing import Any, Dict, Optional
from app.db import db
from app.models import AuditLogEntry

async def record_audit(
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    decision: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        decision=decision,
        metadata=metadata or {},
    )
    await db.audit_logs.insert_one(entry.model_dump())
    return entry


def rule_tests_pass(test_results: Optional[Dict[str, Any]]) -> bool:
    if not test_results:
        return False
    failed = test_results.get("failed", 1)
    coverage = test_results.get("coverage", 0)
    return failed == 0 and coverage >= 80


def redact_evidence_pack(pack: Dict[str, Any], mode: str) -> Dict[str, Any]:
    if mode == "internal":
        return pack

    redacted = {k: v for k, v in pack.items() if k not in {"logs", "contributing_factors"}}
    redacted["logs"] = [
        {
            "event_type": entry.get("event_type"),
            "rule_id": entry.get("rule_id"),
        }
        for entry in pack.get("logs", [])
    ]
    redacted["contributing_factors"] = [
        {"factor": factor.get("factor")}
        for factor in pack.get("contributing_factors", [])
    ]
    return redacted


def compute_checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
