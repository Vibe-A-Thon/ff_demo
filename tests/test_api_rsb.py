from fastapi.testclient import TestClient


def test_merge_requires_conflict_resolution(client: TestClient, auth_headers, in_memory_db):
    package = {
        "id": "pkg-1",
        "name": "Test",
        "version": "1.0.0",
        "description": "",
        "manifest": {"rule_id": "R1"},
        "conflicts": [{"id": "c1"}],
        "validation": {"valid": True},
        "status": "pending",
    }
    in_memory_db.rsb_packages._items.append(package)

    response = client.post("/api/rsb-packages/pkg-1/merge", headers=auth_headers)
    assert response.status_code == 409
