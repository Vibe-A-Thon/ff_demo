from typing import Any, Dict, Iterable, List, Tuple
import re
from app.models import EvidenceItem, ExplanationBundle, EvidenceGraph, EvidenceGraphEdge, EvidenceGraphNode

_NUMERIC_KEYS = {
    "risk_score",
    "avg_score",
    "velocity_score",
    "device_risk_score",
    "geo_risk_score",
    "ip_risk_score",
    "behavior_score",
    "model_score",
    "amount",
    "anomaly_count",
    "anomalies",
}

_CATEGORICAL_KEYS = {
    "device_risk",
    "geo_risk",
    "ip_risk",
    "behavior_risk",
    "risk_level",
}

_RISK_LEVELS = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 0.95}


def _tokenize(text: str) -> List[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9]+", text.lower()) if token]


def _collect_feature_candidates(
    evidence_items: List[EvidenceItem],
    run_metrics: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for item in evidence_items:
        payload = item.payload or {}
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            if key in _NUMERIC_KEYS and isinstance(value, (int, float)):
                candidates.append({
                    "name": key,
                    "value": float(value),
                    "evidence_id": item.evidence_id,
                    "kind": "numeric",
                })
                continue
            if key in _CATEGORICAL_KEYS and isinstance(value, str):
                level = _RISK_LEVELS.get(value.lower())
                if level is not None:
                    candidates.append({
                        "name": key,
                        "value": level,
                        "evidence_id": item.evidence_id,
                        "kind": "categorical",
                        "raw": value,
                    })
                continue
            if key.endswith("_score") and isinstance(value, (int, float)):
                candidates.append({
                    "name": key,
                    "value": float(value),
                    "evidence_id": item.evidence_id,
                    "kind": "numeric",
                })
                continue
            if "risk" in key and isinstance(value, (int, float)):
                candidates.append({
                    "name": key,
                    "value": float(value),
                    "evidence_id": item.evidence_id,
                    "kind": "numeric",
                })
    if run_metrics:
        for key, value in run_metrics.items():
            if key in _NUMERIC_KEYS and isinstance(value, (int, float)):
                candidates.append({
                    "name": key,
                    "value": float(value),
                    "evidence_id": None,
                    "kind": "numeric",
                })
    return candidates


def extract_triggered_rules(events: List[Dict[str, Any]]) -> List[str]:
    rules = set()
    for event in events:
        payload = event.get("payload", {})
        outputs = payload.get("outputs") or {}
        for candidate in [payload.get("rule_id"), outputs.get("rule_id")]:
            if candidate:
                rules.add(candidate)
        rulespec = outputs.get("rulespec") or payload.get("rulespec")
        if isinstance(rulespec, dict):
            rule_id = rulespec.get("rule_id")
            if rule_id:
                rules.add(rule_id)
        triggered_rules = outputs.get("triggered_rules") or payload.get("triggered_rules")
        if isinstance(triggered_rules, list):
            for rule_id in triggered_rules:
                if rule_id:
                    rules.add(rule_id)
    return list(rules)


def extract_artifact_types(events: List[Dict[str, Any]]) -> List[str]:
    types = set()
    for event in events:
        if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
            continue
        payload = event.get("payload", {})
        if payload.get("team"):
            types.add(f"team:{payload.get('team')}")
        if payload.get("agent"):
            types.add(f"agent:{payload.get('agent')}")
        outputs = payload.get("outputs")
        if isinstance(outputs, dict):
            for key in outputs.keys():
                types.add(f"output:{key}")
    return list(types)


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


def build_explanation_bundle(
    run_id: str,
    decision: str,
    evidence_items: List[EvidenceItem],
    run_metrics: Dict[str, Any] | None = None,
) -> ExplanationBundle:
    evidence_types = ", ".join({item.evidence_type for item in evidence_items} or {"signals"})
    summary = f"Decision '{decision}' derived from run evidence for {run_id}."
    details = f"Evidence items include: {evidence_types}."
    confidence_statement = "Confidence reflects observed run telemetry and evidence coverage."
    evidence_graph = build_evidence_graph(run_id, evidence_items)
    counterfactuals = build_counterfactuals(decision, evidence_items, run_metrics)
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


def build_counterfactuals(
    decision: str,
    evidence_items: List[EvidenceItem],
    run_metrics: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    candidates = _collect_feature_candidates(evidence_items, run_metrics)
    if not candidates:
        return []

    expected_outcome = "review"
    if decision == "review":
        expected_outcome = "allow"
    elif decision not in {"block", "review"}:
        expected_outcome = "review"

    counterfactuals: List[Dict[str, Any]] = []
    numeric = sorted([c for c in candidates if c["kind"] == "numeric"], key=lambda x: x["value"], reverse=True)
    categorical = [c for c in candidates if c["kind"] == "categorical"]

    for entry in numeric[:2]:
        value = entry["value"]
        name = entry["name"]
        if "count" in name or "anomal" in name:
            target = max(int(round(value)) - max(1, int(round(value * 0.4))), 0)
            change_value = f"<= {target}"
        else:
            target = round(value * 0.75, 3)
            change_value = f"<= {target}"
        counterfactuals.append(
            {
                "label": f"Reduce {name.replace('_', ' ')}",
                "changes": {name: change_value},
                "expected_outcome": expected_outcome,
                "evidence_links": [entry["evidence_id"]] if entry.get("evidence_id") else [],
            }
        )

    for entry in categorical[:1]:
        name = entry["name"]
        counterfactuals.append(
            {
                "label": f"Lower {name.replace('_', ' ')}",
                "changes": {name: "low"},
                "expected_outcome": expected_outcome,
                "evidence_links": [entry["evidence_id"]] if entry.get("evidence_id") else [],
            }
        )

    return counterfactuals


def build_case_signature(
    run_id: str,
    decision: str,
    events: List[Dict[str, Any]],
    evidence_items: List[EvidenceItem],
    run_metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    rules = set(extract_triggered_rules(events))
    artifacts = set(extract_artifact_types(events))
    token_source = " ".join([item.summary for item in evidence_items])
    tokens = set(_tokenize(token_source))
    avg_score = None
    if run_metrics and isinstance(run_metrics.get("avg_score"), (int, float)):
        avg_score = float(run_metrics.get("avg_score"))
    return {
        "run_id": run_id,
        "decision": decision,
        "rules": rules,
        "artifacts": artifacts,
        "tokens": tokens,
        "avg_score": avg_score,
    }


def build_pack_signature(pack: Dict[str, Any]) -> Dict[str, Any]:
    rules = set(pack.get("triggered_rules") or [])
    artifacts = set()
    for artifact in pack.get("artifacts") or []:
        event_type = artifact.get("event_type")
        if event_type:
            artifacts.add(f"event:{event_type}")
        agent = artifact.get("agent")
        if agent:
            artifacts.add(f"agent:{agent}")
        team = artifact.get("team")
        if team:
            artifacts.add(f"team:{team}")
    summary = pack.get("narrative", "")
    xai_bundle = pack.get("xai_bundle") or {}
    if xai_bundle.get("summary"):
        summary = f"{summary} {xai_bundle.get('summary')}"
    tokens = set(_tokenize(summary))
    metrics = pack.get("metrics") or {}
    avg_score = metrics.get("avg_score")
    decision = metrics.get("decision") or xai_bundle.get("decision_id")
    if isinstance(avg_score, (int, float)):
        avg_score = float(avg_score)
    else:
        avg_score = None
    return {
        "pack_id": pack.get("id"),
        "run_id": pack.get("run_id"),
        "battle_id": pack.get("battle_id"),
        "decision": decision,
        "rules": rules,
        "artifacts": artifacts,
        "tokens": tokens,
        "avg_score": avg_score,
    }


def score_case_similarity(current: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
        left_set = set(left)
        right_set = set(right)
        if not left_set or not right_set:
            return 0.0
        return len(left_set & right_set) / max(len(left_set | right_set), 1)

    rules_score = jaccard(current.get("rules", []), candidate.get("rules", []))
    artifact_score = jaccard(current.get("artifacts", []), candidate.get("artifacts", []))
    token_score = jaccard(current.get("tokens", []), candidate.get("tokens", []))
    decision_match = 1.0 if current.get("decision") and current.get("decision") == candidate.get("decision") else 0.0

    current_score = current.get("avg_score")
    candidate_score = candidate.get("avg_score")
    if isinstance(current_score, (int, float)) and isinstance(candidate_score, (int, float)):
        score_gap = abs(current_score - candidate_score)
        metric_score = max(1.0 - min(score_gap, 1.0), 0.0)
    else:
        metric_score = 0.0

    weights = {
        "rules": 0.3,
        "artifacts": 0.2,
        "tokens": 0.2,
        "decision": 0.2,
        "metric": 0.1,
    }
    similarity = (
        rules_score * weights["rules"]
        + artifact_score * weights["artifacts"]
        + token_score * weights["tokens"]
        + decision_match * weights["decision"]
        + metric_score * weights["metric"]
    )
    details = {
        "rules": rules_score,
        "artifacts": artifact_score,
        "tokens": token_score,
        "decision": decision_match,
        "metric": metric_score,
        "matched_rules": list(set(current.get("rules", [])) & set(candidate.get("rules", []))),
    }
    return round(similarity, 4), details
