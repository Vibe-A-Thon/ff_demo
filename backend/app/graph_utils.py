import uuid
from typing import Any, Dict, List
from app.models import EvaluationReport, QualityCheckResult


def build_run_graph(run_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    def add_node(node_id: str, node_type: str, label: str) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "type": node_type, "label": label}

    run_node = f"run:{run_id}"
    add_node(run_node, "run", f"Run {run_id}")

    for event in events:
        event_id = event.get("id") or str(uuid.uuid4())
        event_type = event.get("event_type", "event")
        event_node = f"event:{event_id}"
        add_node(event_node, "event", event_type)
        edges.append({"source": run_node, "target": event_node, "type": "emits"})

        payload = event.get("payload", {})
        agent = payload.get("agent")
        if agent:
            agent_node = f"agent:{agent}"
            add_node(agent_node, "agent", agent)
            edges.append({"source": agent_node, "target": event_node, "type": "produces"})

        tool = payload.get("tool")
        if tool:
            tool_node = f"tool:{tool}"
            add_node(tool_node, "tool", tool)
            edges.append({"source": tool_node, "target": event_node, "type": "feeds"})

    return {"nodes": list(nodes.values()), "edges": edges}


def summarize_run_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    last_metrics = run.get("last_metrics", {})
    return {
        "avg_score": last_metrics.get("avg_score", 0),
        "decision": run.get("last_decision", "unknown"),
        "actions": last_metrics.get("actions", 0),
        "steps": run.get("step_count", 0),
    }


def run_quality_checks(run: Dict[str, Any], events: List[Dict[str, Any]]) -> QualityCheckResult:
    issues: List[Dict[str, Any]] = []
    last_decision = run.get("last_decision")
    if not last_decision:
        issues.append({"check": "decision_present", "status": "fail", "message": "Missing decision"})
    else:
        issues.append({"check": "decision_present", "status": "pass"})

    evidence_events = [e for e in events if e.get("event_type") == "xai.generated"]
    if not evidence_events:
        issues.append({"check": "xai_generated", "status": "warn", "message": "No XAI bundle generated"})
    else:
        issues.append({"check": "xai_generated", "status": "pass"})

    status = "pass" if all(i["status"] == "pass" for i in issues) else "warn"
    return QualityCheckResult(run_id=run.get("id", "unknown"), status=status, checks=issues)


def build_evaluation_report(run: Dict[str, Any]) -> EvaluationReport:
    metrics = summarize_run_metrics(run)
    summary = "Run evaluation completed with synthetic checks."
    return EvaluationReport(run_id=run.get("id", "unknown"), summary=summary, metrics=metrics)
