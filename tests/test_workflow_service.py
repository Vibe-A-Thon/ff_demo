from app import db as db_module
from app.workflow_service import compute_governance_status


def test_compute_governance_status_pending(in_memory_db):
    db_module.db = in_memory_db
    in_memory_db.approvals._items.append(
        {
            "resource_type": "run",
            "resource_id": "run-1",
            "action": "rulespec_pending_approval",
            "status": "pending",
        }
    )
    status = __import__("asyncio").run(compute_governance_status("run-1"))
    assert status["status"] == "PROCEED_WITH_REVIEW"
