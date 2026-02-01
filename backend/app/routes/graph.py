"""Run graph routes.

Provides graph and comparison views for war loop runs.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.graph_utils import build_run_graph, summarize_run_metrics
from app.graph_utils import build_lineage_graph
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.get("/runs/{run_id}/graph")
async def get_run_graph(run_id: str, current_user: dict = Depends(require_permission("graph:read"))):
    """Build a graph for a run.

    Args:
        run_id: Run identifier.

    Returns:
        dict: Graph payload containing nodes and edges.

    Raises:
        HTTPException: If the run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    graph = build_run_graph(run_id, events)
    await record_audit(
        current_user.get("id", "unknown"),
        "graph.run.generated",
        "run",
        run_id,
        metadata={"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))},
    )
    logger.info(
        "graph.run.generated",
        extra={"payload": {"run_id": run_id, "nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))}},
    )
    return {"run_id": run_id, "graph": graph}

@router.get("/runs/{run_id}/lineage-graph")
async def get_run_lineage_graph(run_id: str, current_user: dict = Depends(require_permission("graph:read"))):
    """Build a lineage graph for a run.

    Args:
        run_id: Run identifier.

    Returns:
        dict: Lineage graph payload.

    Raises:
        HTTPException: If the run is not found.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    tasks = await db.agent_tasks.find({"run_id": run_id}, {"_id": 0}).to_list(500)
    artifacts = await db.agent_artifacts.find({"run_id": run_id}, {"_id": 0}).to_list(1000)
    evidence_packs = await db.evidence_packs.find({"run_id": run_id}, {"_id": 0}).to_list(50)

    graph = build_lineage_graph(run_id, events, tasks, artifacts, evidence_packs)
    await record_audit(
        current_user.get("id", "unknown"),
        "graph.lineage.generated",
        "run",
        run_id,
        metadata={"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))},
    )
    return graph

@router.get("/evidence-packs/{pack_id}/lineage-graph")
async def get_evidence_lineage_graph(pack_id: str, current_user: dict = Depends(require_permission("graph:read"))):
    """Build a lineage graph for an evidence pack.

    Args:
        pack_id: Evidence pack identifier.

    Returns:
        dict: Lineage graph payload.

    Raises:
        HTTPException: If the evidence pack is not found.
    """
    pack = await db.evidence_packs.find_one({"id": pack_id}, {"_id": 0})
    if not pack:
        raise HTTPException(status_code=404, detail="Evidence pack not found")
    run_id = pack.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="Evidence pack is not linked to a run")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(500)
    tasks = await db.agent_tasks.find({"run_id": run_id}, {"_id": 0}).to_list(500)
    artifacts = await db.agent_artifacts.find({"run_id": run_id}, {"_id": 0}).to_list(1000)
    graph = build_lineage_graph(run_id, events, tasks, artifacts, [pack])

    await record_audit(
        current_user.get("id", "unknown"),
        "graph.lineage.evidence.generated",
        "evidence_pack",
        pack_id,
        metadata={"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))},
    )
    return graph
@router.get("/runs/compare")
async def compare_runs(run_a: str, run_b: str, current_user: dict = Depends(require_permission("graph:read"))):
    """Compare two runs and return metric deltas.

    Args:
        run_a: First run identifier.
        run_b: Second run identifier.

    Returns:
        dict: Metrics for both runs and computed delta.

    Raises:
        HTTPException: If either run is not found.
    """
    run_a_doc = await db.runs.find_one({"id": run_a}, {"_id": 0})
    run_b_doc = await db.runs.find_one({"id": run_b}, {"_id": 0})

    if not run_a_doc or not run_b_doc:
        raise HTTPException(status_code=404, detail="Run not found")

    metrics_a = summarize_run_metrics(run_a_doc)
    metrics_b = summarize_run_metrics(run_b_doc)

    delta = {
        "avg_score": metrics_b["avg_score"] - metrics_a["avg_score"],
        "actions": metrics_b["actions"] - metrics_a["actions"],
        "steps": metrics_b["steps"] - metrics_a["steps"],
        "decision_changed": metrics_a["decision"] != metrics_b["decision"],
    }

    logger.info(
        "graph.runs.compared",
        extra={"payload": {"run_a": run_a, "run_b": run_b, "decision_changed": delta["decision_changed"]}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "graph.runs.compared",
        "run",
        f"{run_a}:{run_b}",
        metadata={"decision_changed": delta["decision_changed"]},
    )
    return {"run_a": metrics_a, "run_b": metrics_b, "delta": delta}
