from fastapi import APIRouter
from app.db import db
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/metrics/dashboard")
async def get_dashboard_metrics():
    battles = await db.battles.find({}, {"_id": 0}).to_list(100)
    rules = await db.rules.find({}, {"_id": 0}).to_list(100)

    completed_battles = [b for b in battles if b.get("status") == "completed"]
    total_success = sum(b.get("metrics", {}).get("success_rate", 0) for b in completed_battles)
    avg_success = total_success / len(completed_battles) if completed_battles else 0

    payload = {
        "total_battles": len(battles),
        "completed_battles": len(completed_battles),
        "running_battles": len([b for b in battles if b.get("status") == "running"]),
        "avg_success_rate": round(avg_success, 2),
        "total_rules": len(rules),
        "active_rules": len([r for r in rules if r.get("status") == "active"]),
        "patterns_learned": sum(b.get("metrics", {}).get("patterns_learned", 0) for b in completed_battles),
        "avg_time_to_immunity": round(sum(b.get("metrics", {}).get("time_to_immunity", 0) for b in completed_battles) / max(len(completed_battles), 1), 2),
        "time_series": [
            {
                "timestamp": b.get("created_at"),
                "success_rate": b.get("metrics", {}).get("success_rate", 0),
                "time_to_immunity": b.get("metrics", {}).get("time_to_immunity", 0),
            }
            for b in completed_battles[-20:]
        ],
    }
    logger.info(
        "metrics.dashboard.generated",
        extra={"payload": {"total_battles": payload["total_battles"], "total_rules": payload["total_rules"]}},
    )
    return payload
