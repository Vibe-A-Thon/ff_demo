"""Run evaluation and quality routes."""

from fastapi import APIRouter, HTTPException
from app.db import db
from app.graph_utils import run_quality_checks, build_evaluation_report
from app.run_helpers import record_run_event
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/runs/{run_id}/quality")
async def get_run_quality(run_id: str):
    """Compute and persist quality checks for a run.

    Args:
        run_id: Run identifier.

    Returns:
        QualityCheckResult: Computed quality checks.

    Raises:
        HTTPException: If the run does not exist.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    events = await db.run_events.find({"run_id": run_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    result = run_quality_checks(run, events)
    await db.quality_checks.insert_one(result.model_dump())
    logger.info(
        "evaluation.quality.completed",
        extra={"payload": {"run_id": run_id, "status": result.status}},
    )
    return result

@router.get("/runs/{run_id}/evaluate")
async def evaluate_run(run_id: str):
    """Generate and persist an evaluation report for a run.

    Args:
        run_id: Run identifier.

    Returns:
        EvaluationReport: Evaluation report payload.

    Raises:
        HTTPException: If the run does not exist.
    """
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    report = build_evaluation_report(run)
    await db.evaluations.insert_one(report.model_dump())
    await record_run_event(run_id, "evaluation.completed", {"report_id": report.report_id})
    logger.info(
        "evaluation.report.completed",
        extra={"payload": {"run_id": run_id, "report_id": report.report_id}},
    )
    return report
