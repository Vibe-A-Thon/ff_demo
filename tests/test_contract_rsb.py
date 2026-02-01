import io
import json
import zipfile

from fastapi.testclient import TestClient


def _build_rsb_zip() -> bytes:
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "rule_id": "RULE-100",
                    "name": "Velocity",
                    "rule_version": "1.0.0",
                    "attack_type": "velocity",
                }
            ),
        )
        zf.writestr("rule/specification.json", json.dumps({"rule_id": "RULE-100"}))
        zf.writestr("rule/rule.json", json.dumps({"rule_id": "RULE-100"}))
        zf.writestr("rule/description.md", "desc")
        zf.writestr("rule/rule_Patch.py", "# patch")
        zf.writestr("code/ruleC_RULE-100.py", "print('ok')")
        zf.writestr("tests/ruleUT_example.py", "def test_ok():\n    assert True\n")
    memory.seek(0)
    return memory.read()


def test_rsb_upload_contract(client: TestClient, auth_headers):
    payload = _build_rsb_zip()
    files = {"file": ("sample.rsb", payload, "application/zip")}
    response = client.post("/api/rsb-packages/upload", files=files, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["valid"] is True
    assert data["manifest"]["rule_id"] == "RULE-100"
    assert data["status"] == "pending"


def test_rsb_merge_rejects_invalid_package(client: TestClient, auth_headers, in_memory_db):
    in_memory_db.rsb_packages._items.append(
        {
            "id": "pkg-invalid",
            "manifest": {"rule_id": "RULE-200"},
            "validation": {"valid": False},
            "conflicts": [],
            "status": "pending",
        }
    )
    response = client.post("/api/rsb-packages/pkg-invalid/merge", headers=auth_headers)
    assert response.status_code == 400


def test_rsb_merge_requires_conflict_resolution(client: TestClient, auth_headers, in_memory_db):
    in_memory_db.rsb_packages._items.append(
        {
            "id": "pkg-conflict",
            "manifest": {"rule_id": "RULE-201"},
            "validation": {"valid": True},
            "conflicts": [{"id": "c1"}],
            "status": "pending",
        }
    )
    response = client.post("/api/rsb-packages/pkg-conflict/merge", headers=auth_headers)
    assert response.status_code == 409


def test_rsb_apply_patch_updates_version(client: TestClient, auth_headers, in_memory_db):
    in_memory_db.rsb_packages._items.append(
        {
            "id": "pkg-apply",
            "name": "Package",
            "version": "1.0.0",
            "manifest": {"rule_id": "RULE-300"},
            "rule_spec": {"rule_id": "RULE-300"},
            "rule_definition": {"rule_id": "RULE-300"},
            "description_md": "desc",
            "patch_script": "# patch",
            "code": "print('ok')",
            "code_patch": "print('patched')",
            "test_results": {"unit_tests": {"passed": 1, "failed": 0, "total": 1}},
            "conflicts": [],
            "validation": {"valid": True},
            "status": "tested",
        }
    )
    response = client.post(
        "/api/rsb-packages/pkg-apply/apply-patch",
        json={"decision": "accepted", "commit_message": "Patch applied"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"].startswith("1.0.")
    assert data["patch_decision"] == "accepted"
