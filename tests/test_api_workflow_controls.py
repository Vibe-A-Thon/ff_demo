from fastapi.testclient import TestClient


def test_workflow_control_endpoints(client: TestClient, auth_headers, in_memory_db):
    run_id = "run-ctrl"
    in_memory_db.runs._items.append({"id": run_id, "workflow_state": "incident_created", "workflow_status": "running"})

    freeze = client.post(f"/api/workflow/{run_id}/freeze", json={"actor_id": "user"}, headers=auth_headers)
    assert freeze.status_code == 200

    rollback = client.post(f"/api/workflow/{run_id}/rollback", json={"actor_id": "user"}, headers=auth_headers)
    assert rollback.status_code == 200

    reset = client.post(f"/api/workflow/{run_id}/reset", json={"actor_id": "user"}, headers=auth_headers)
    assert reset.status_code == 200
