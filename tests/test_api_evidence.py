from fastapi.testclient import TestClient


def test_external_export_requires_approval(client: TestClient, auth_headers, in_memory_db):
    pack_id = "pack-1"
    in_memory_db.evidence_packs._items.append(
        {
            "id": pack_id,
            "narrative": "test",
            "triggered_rules": [],
            "contributing_factors": [],
            "confidence": 0.9,
            "logs": [],
            "checksum": "",
        }
    )

    response = client.get(f"/api/evidence-packs/{pack_id}/export?mode=external", headers=auth_headers)
    assert response.status_code == 403
