from fastapi.testclient import TestClient


def test_runs_start_step_export(client: TestClient, auth_headers):
    start = client.post(
        "/api/runs/start",
        json={"scenario_id": "demo", "mode": "auto"},
        headers=auth_headers,
    )
    assert start.status_code == 200
    run_id = start.json()["id"]

    step = client.post(f"/api/runs/{run_id}/step", headers=auth_headers)
    assert step.status_code == 200

    export = client.get(f"/api/runs/{run_id}/export-brc", headers=auth_headers)
    assert export.status_code == 200
    assert export.headers.get("content-disposition")
