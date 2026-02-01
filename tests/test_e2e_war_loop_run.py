from fastapi.testclient import TestClient


def test_war_loop_run_progression(client: TestClient, auth_headers, in_memory_db):
    start = client.post(
        "/api/runs/start",
        json={"scenario_id": "war-loop", "mode": "auto", "seed": 123},
        headers=auth_headers,
    )
    assert start.status_code == 200
    run_id = start.json()["id"]

    # Ensure approvals exist for gated stages to avoid awaiting approval
    in_memory_db.approvals._items.extend(
        [
            {"resource_type": "run", "resource_id": run_id, "action": "orange_review_approve", "status": "approved"},
            {"resource_type": "run", "resource_id": run_id, "action": "white_compliance_audit", "status": "approved"},
        ]
    )

    stages = []
    for _ in range(10):
        step = client.post(f"/api/runs/{run_id}/step", headers=auth_headers)
        assert step.status_code == 200
        payload = step.json()
        stages.append(payload.get("stage"))
        if payload.get("next_stage") == "done":
            break

    assert "red_simulate_attack" in stages
    assert "blue_detect_respond" in stages

    run_response = client.get(f"/api/runs/{run_id}", headers=auth_headers)
    assert run_response.status_code == 200
    events = run_response.json()["events"]
    assert any(event.get("event_type") == "stage.changed" for event in events)
