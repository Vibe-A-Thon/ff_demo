from fastapi.testclient import TestClient

from app.security import create_token
from tests.fixtures import seed_user


def test_rbac_denies_rules_write(client: TestClient, in_memory_db):
    user = seed_user(in_memory_db, role="bank_fraud_operator")
    token = create_token(user["id"], user["role"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/rules",
        json={
            "name": "rule",
            "description": "desc",
            "rule_type": "velocity",
            "conditions": [],
            "actions": [],
            "priority": 1,
        },
        headers=headers,
    )
    assert response.status_code == 403
