from typing import Any, Dict, List
from app.models import EvidenceItem, ExplanationBundle


def build_evidence_items(events: List[Dict[str, Any]], max_items: int = 6) -> List[EvidenceItem]:
    evidence_items: List[EvidenceItem] = []
    for event in events[-max_items:]:
        summary = event.get("event_type", "signal")
        payload = event.get("payload", {})
        evidence_items.append(
            EvidenceItem(
                evidence_type=summary,
                summary=f"Event {summary} recorded",
                source_tool=payload.get("tool"),
                source_run=event.get("run_id"),
                source_step=payload.get("step"),
                payload=payload,
            )
        )
    return evidence_items


def build_explanation_bundle(run_id: str, decision: str, evidence_items: List[EvidenceItem]) -> ExplanationBundle:
    summary = f"Decision '{decision}' generated from synthetic evidence for run {run_id}."
    details = "Evidence items include simulator outputs, risk scores, and response actions."
    confidence_statement = "Confidence is based on deterministic synthetic scoring."
    return ExplanationBundle(
        decision_id=decision,
        summary=summary,
        details=details,
        evidence=evidence_items,
        confidence_statement=confidence_statement,
    )
