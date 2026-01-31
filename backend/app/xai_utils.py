from typing import Any, Dict, List
from app.models import EvidenceItem, ExplanationBundle, EvidenceGraph, EvidenceGraphEdge, EvidenceGraphNode


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
    evidence_graph = build_evidence_graph(run_id, evidence_items)
    counterfactuals = build_counterfactuals(decision)
    return ExplanationBundle(
        decision_id=decision,
        summary=summary,
        details=details,
        evidence=evidence_items,
        confidence_statement=confidence_statement,
        evidence_graph=evidence_graph.model_dump(),
        counterfactuals=counterfactuals,
    )


def build_evidence_graph(run_id: str, evidence_items: List[EvidenceItem]) -> EvidenceGraph:
    nodes: List[EvidenceGraphNode] = [
        EvidenceGraphNode(node_id=run_id, node_type="Run", label=f"Run {run_id[:8]}")
    ]
    edges: List[EvidenceGraphEdge] = []
    for item in evidence_items:
        node_id = item.evidence_id
        nodes.append(
            EvidenceGraphNode(
                node_id=node_id,
                node_type=item.evidence_type,
                label=item.summary,
                metadata={"source_tool": item.source_tool},
            )
        )
        edges.append(
            EvidenceGraphEdge(
                source=run_id,
                target=node_id,
                relation="SUPPORTED_BY",
            )
        )
    return EvidenceGraph(nodes=nodes, edges=edges)


def build_counterfactuals(decision: str) -> List[Dict[str, Any]]:
    if decision == "block":
        return [
            {
                "label": "Lower velocity below threshold",
                "changes": {"velocity_score": "< 0.6"},
                "expected_outcome": "review",
            },
            {
                "label": "Clean device reputation",
                "changes": {"device_risk": "low"},
                "expected_outcome": "allow",
            },
        ]
    if decision == "review":
        return [
            {
                "label": "Reduce anomalous signals",
                "changes": {"anomaly_count": "-2"},
                "expected_outcome": "allow",
            }
        ]
    return [
        {
            "label": "Increase anomaly confidence",
            "changes": {"risk_score": "> 0.8"},
            "expected_outcome": "review",
        }
    ]
