from fastapi.testclient import TestClient


def test_generate_evidence_pack_from_run(client: TestClient, auth_headers, in_memory_db):
    run_id = "run-evidence"
    in_memory_db.runs._items.append(
        {
            "id": run_id,
            "workflow_state": "incident_created",
            "workflow_history": [],
            "current_stage": "blue_detect_respond",
            "last_metrics": {"avg_score": 0.4},
        }
    )

    response = client.post(f"/api/evidence-packs/generate/run/{run_id}", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["checksum"]
