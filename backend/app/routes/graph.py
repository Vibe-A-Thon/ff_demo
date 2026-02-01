from fastapi import APIRouter, HTTPException
from app.db import db
from app.graph_utils import build_run_graph, summarize_run_metrics
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/runs/{run_id}/graph")
async def get_run_graph(run_id: str):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    graph = build_run_graph(run_id, events)
    logger.info(
        "graph.run.generated",
        extra={"payload": {"run_id": run_id, "nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))}},
    )
    return {"run_id": run_id, "graph": graph}

@router.get("/runs/compare")
async def compare_runs(run_a: str, run_b: str):
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
    return {"run_a": metrics_a, "run_b": metrics_b, "delta": delta}
