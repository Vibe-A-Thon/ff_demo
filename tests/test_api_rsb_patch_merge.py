from fastapi.testclient import TestClient


def test_rsb_patch_and_merge_flow(client: TestClient, auth_headers, in_memory_db):
    package_id = "pkg-flow"
    in_memory_db.rsb_packages._items.append(
        {
            "id": package_id,
            "name": "Package",
            "version": "1.0.0",
            "manifest": {"rule_id": "RULE-400"},
            "rule_spec": {"rule_id": "RULE-400"},
            "rule_definition": {"rule_id": "RULE-400"},
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

    apply_patch = client.post(
        f"/api/rsb-packages/{package_id}/apply-patch",
        json={"decision": "accepted", "commit_message": "apply"},
        headers=auth_headers,
    )
    assert apply_patch.status_code == 200

    stage = client.post(f"/api/rsb-packages/{package_id}/stage", headers=auth_headers)
    assert stage.status_code == 200

    merge = client.post(f"/api/rsb-packages/{package_id}/merge", headers=auth_headers)
    assert merge.status_code == 200
    assert merge.json()["status"] == "merged"


def test_rsb_resolve_conflicts(client: TestClient, auth_headers, in_memory_db):
    package_id = "pkg-conflicts"
    in_memory_db.rsb_packages._items.append(
        {
            "id": package_id,
            "manifest": {"rule_id": "RULE-401"},
            "validation": {"valid": True},
            "conflicts": [{"id": "c1"}],
            "status": "pending",
        }
    )

    resolve = client.post(
        f"/api/rsb-packages/{package_id}/resolve-conflicts",
        json={"c1": "keep_current"},
        headers=auth_headers,
    )
    assert resolve.status_code == 200
    assert resolve.json()["conflict_resolutions"]["c1"] == "keep_current"
