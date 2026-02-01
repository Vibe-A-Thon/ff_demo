"""Graph utilities for runs and evaluations."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from app.models import EvaluationReport, QualityCheckResult


def build_run_graph(run_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a graph representation of a run.

    Args:
        run_id: Run identifier.
        events: Run events.

    Returns:
        Dict[str, Any]: Graph payload with nodes and edges.

    Raises:
        None: No explicit exceptions are raised.
    """
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


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def build_lineage_graph(
    run_id: str,
    events: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    artifacts: List[Dict[str, Any]],
    evidence_packs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build an end-to-end artifact lineage graph.

    Args:
        run_id: Run identifier.
        events: Run events.
        tasks: Agent tasks for the run.
        artifacts: Agent artifacts for the run.
        evidence_packs: Evidence packs linked to the run.

    Returns:
        Dict[str, Any]: Graph payload with nodes and edges.

    Raises:
        None: No explicit exceptions are raised.
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    def add_node(node_id: str, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        if node_id not in nodes:
            nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                "metadata": metadata or {},
            }

    run_node = f"run:{run_id}"
    add_node(run_node, "run", f"Run {run_id}")

    stage_events = [event for event in events if event.get("event_type") == "stage.changed"]
    stage_events.sort(key=lambda item: item.get("created_at") or "")
    stage_windows: List[Tuple[str, Optional[datetime], Optional[datetime]]] = []
    for idx, event in enumerate(stage_events):
        payload = event.get("payload", {})
        stage_name = payload.get("stage", "stage")
        step = payload.get("step", idx + 1)
        stage_id = f"stage:{stage_name}:{step}"
        add_node(stage_id, "stage", stage_name, {"step": step})
        edges.append({"source": run_node, "target": stage_id, "type": "has_stage"})
        start_ts = _parse_ts(event.get("created_at"))
        end_ts = _parse_ts(stage_events[idx + 1].get("created_at")) if idx + 1 < len(stage_events) else None
        stage_windows.append((stage_id, start_ts, end_ts))

    def resolve_stage(ts_value: Optional[str]) -> Optional[str]:
        ts = _parse_ts(ts_value)
        if not ts:
            return None
        for stage_id, start_ts, end_ts in stage_windows:
            if start_ts and ts >= start_ts and (end_ts is None or ts < end_ts):
                return stage_id
        return None

    for task in tasks:
        task_id = task.get("task_id")
        if not task_id:
            continue
        task_node = f"task:{task_id}"
        add_node(task_node, "task", task.get("task_type", "task"), {"team": task.get("team_id")})
        edges.append({"source": run_node, "target": task_node, "type": "requests"})
        stage_id = resolve_stage(task.get("created_at"))
        if stage_id:
            edges.append({"source": stage_id, "target": task_node, "type": "dispatches"})

    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id")
        if not artifact_id:
            continue
        artifact_node = f"artifact:{artifact_id}"
        add_node(
            artifact_node,
            "artifact",
            artifact.get("artifact_type", "artifact"),
            {"agent": artifact.get("agent_id"), "team": artifact.get("team_id")},
        )
        edges.append({"source": run_node, "target": artifact_node, "type": "produces"})
        task_id = artifact.get("task_id")
        if task_id:
            edges.append({"source": f"task:{task_id}", "target": artifact_node, "type": "outputs"})
        stage_id = resolve_stage(artifact.get("created_at"))
        if stage_id:
            edges.append({"source": stage_id, "target": artifact_node, "type": "emits"})
        agent_id = artifact.get("agent_id")
        if agent_id:
            agent_node = f"agent:{agent_id}"
            add_node(agent_node, "agent", agent_id)
            edges.append({"source": agent_node, "target": artifact_node, "type": "produces"})

        lineage_inputs = artifact.get("lineage", {}).get("inputs", [])
        for lineage in lineage_inputs:
            parent_id = None
            if isinstance(lineage, dict):
                parent_id = lineage.get("artifact_id")
            if parent_id:
                parent_node = f"artifact:{parent_id}"
                add_node(parent_node, "artifact", lineage.get("artifact_type", "artifact"))
                edges.append({"source": parent_node, "target": artifact_node, "type": "lineage"})

    for pack in evidence_packs:
        pack_id = pack.get("id")
        if not pack_id:
            continue
        pack_node = f"evidence:{pack_id}"
        add_node(pack_node, "evidence_pack", f"Evidence {pack_id}")
        edges.append({"source": run_node, "target": pack_node, "type": "evidence_pack"})
        for stage_id, _, _ in stage_windows:
            edges.append({"source": stage_id, "target": pack_node, "type": "evidence_summary"})
        for artifact in artifacts:
            artifact_id = artifact.get("artifact_id")
            if artifact_id:
                edges.append({"source": f"artifact:{artifact_id}", "target": pack_node, "type": "included_in"})

    return {"nodes": list(nodes.values()), "edges": edges}


def summarize_run_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize run metrics into a compact payload.

    Args:
        run: Run document.

    Returns:
        Dict[str, Any]: Summary metrics.

    Raises:
        None: No explicit exceptions are raised.
    """
    last_metrics = run.get("last_metrics", {})
    return {
        "avg_score": last_metrics.get("avg_score", 0),
        "decision": run.get("last_decision", "unknown"),
        "actions": last_metrics.get("actions", 0),
        "steps": run.get("step_count", 0),
    }


def run_quality_checks(run: Dict[str, Any], events: List[Dict[str, Any]]) -> QualityCheckResult:
    """Run synthetic quality checks.

    Args:
        run: Run document.
        events: Run events.

    Returns:
        QualityCheckResult: Quality check result.

    Raises:
        None: No explicit exceptions are raised.
    """
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
    """Build an evaluation report for a run.

    Args:
        run: Run document.

    Returns:
        EvaluationReport: Evaluation report.

    Raises:
        None: No explicit exceptions are raised.
    """
    metrics = summarize_run_metrics(run)
    summary = "Run evaluation completed with synthetic checks."
    return EvaluationReport(run_id=run.get("id", "unknown"), summary=summary, metrics=metrics)
