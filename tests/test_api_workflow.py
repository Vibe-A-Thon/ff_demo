from fastapi.testclient import TestClient


def test_workflow_status_returns_governance(client: TestClient, auth_headers, in_memory_db):
    run_id = "run-1"
    in_memory_db.runs._items.append({"id": run_id, "workflow_state": "incident_created", "workflow_status": "running"})
    in_memory_db.approvals._items.append(
        {
            "resource_type": "run",
            "resource_id": run_id,
            "action": "rulespec_pending_approval",
            "status": "pending",
        }
    )

    response = client.get(f"/api/workflow/{run_id}/status", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["governance"]["status"] == "PROCEED_WITH_REVIEW"
