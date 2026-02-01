from fastapi.testclient import TestClient


def test_battle_flow_e2e(client: TestClient, auth_headers):
    create = client.post(
        "/api/battles",
        json={"scenario_name": "Test Scenario", "parameters": {}},
        headers=auth_headers,
    )
    assert create.status_code == 200
    battle_id = create.json()["id"]

    start = client.post(f"/api/battles/{battle_id}/start", headers=auth_headers)
    assert start.status_code == 200
    assert start.json()["status"] == "running"

    stop = client.post(f"/api/battles/{battle_id}/stop", headers=auth_headers)
    assert stop.status_code == 200
    assert stop.json()["status"] == "completed"
