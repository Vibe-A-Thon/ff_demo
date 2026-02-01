from fastapi.testclient import TestClient


def test_approvals_create_and_decide(client: TestClient, auth_headers):
    create = client.post(
        "/api/approvals",
        json={
            "resource_type": "rule",
            "resource_id": "rule-1",
            "action": "approve",
            "requestor_id": "user-1",
            "metadata": {"note": "test"},
        },
        headers=auth_headers,
    )
    assert create.status_code == 200
    approval_id = create.json()["id"]

    approve = client.post(f"/api/approvals/{approval_id}/approve?approver_id=user-2", headers=auth_headers)
    assert approve.status_code == 200

    reject = client.post(f"/api/approvals/{approval_id}/reject?approver_id=user-2", headers=auth_headers)
    assert reject.status_code == 200
