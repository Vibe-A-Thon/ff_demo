from fastapi.testclient import TestClient


def test_route_agent_tasks(client: TestClient, auth_headers, in_memory_db):
    payload = {
        "run_id": "run-1",
        "team_id": "red",
        "objective": "Route tasks for red team",
        "max_agents": 2,
        "auto_execute": False,
    }
    response = client.post("/api/agents/route", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 2


def test_orchestrate_team_tasks(client: TestClient, auth_headers, in_memory_db):
    payload = {
        "run_id": "run-2",
        "objective": "Cross-team objective",
        "teams": ["red", "blue"],
        "max_agents_per_team": 1,
        "auto_execute": True,
    }
    response = client.post("/api/agents/orchestrate", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 2
    assert "results" in data
    assert len(data["results"]) > 0


def test_replay_run(client: TestClient, auth_headers, in_memory_db):
    run_id = "run-replay-1"
    in_memory_db.runs._items.append({"id": run_id, "seed": 123, "mode": "auto"})
    response = client.post(
        f"/api/runs/{run_id}/replay",
        headers=auth_headers,
        json={"seed": 999, "reset_events": True, "clear_agent_tasks": True, "clear_agent_artifacts": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["seed"] == 999
    assert data["status"] == "replayed"
