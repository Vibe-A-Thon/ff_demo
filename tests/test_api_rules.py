from fastapi.testclient import TestClient


def test_create_and_get_rule(client: TestClient, auth_headers):
    create = client.post(
        "/api/rules",
        json={
            "name": "velocity",
            "description": "desc",
            "rule_type": "velocity",
            "conditions": [],
            "actions": [],
            "priority": 1,
        },
        headers=auth_headers,
    )
    assert create.status_code == 200
    rule = create.json()

    fetched = client.get(f"/api/rules/{rule['id']}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "velocity"
