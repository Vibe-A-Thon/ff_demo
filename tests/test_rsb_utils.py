import io
import json
import zipfile

from app.rsb_utils import (
    build_rsb_tree,
    validate_rsb_payload,
    bump_patch_version,
    build_rsb_archive,
    read_zip_json,
    read_zip_text,
    find_first_match,
    build_test_results,
)


def test_build_rsb_tree():
    tree = build_rsb_tree(["rule/specification.json", "code/ruleC_X.py"])
    assert any(node["name"].startswith("rule/") for node in tree)


def test_validate_rsb_payload_missing_files():
    validation = validate_rsb_payload({}, {}, {}, [])
    assert validation["valid"] is False
    assert any("manifest.json" in error for error in validation["errors"])


def test_bump_patch_version():
    assert bump_patch_version("1.2.3") == "1.2.4"


def test_build_rsb_archive_contains_manifest():
    archive = build_rsb_archive(
        manifest={"rule_id": "R1", "rule_version": "1.0.0"},
        rule_spec={"rule_id": "R1"},
        rule_def={"rule_id": "R1"},
        description_md="desc",
        patch_script="",
        code="print('ok')",
        code_patch=None,
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["rule_id"] == "R1"


def test_read_zip_helpers_and_find_match(tmp_path):
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"rule_id": "R1"}))
        zf.writestr("code/ruleC_R1.py", "print('ok')")

    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = read_zip_json(zf, "manifest.json")
        code = read_zip_text(zf, "code/ruleC_R1.py")

    assert manifest is not None
    assert code is not None
    assert manifest["rule_id"] == "R1"
    assert "print" in code
    match = find_first_match(["code/ruleC_R1.py"], "code/", ".py")
    assert match == "code/ruleC_R1.py"


def test_build_test_results_deterministic():
    file_names = ["tests/ruleUT_example.py", "tests/ruleIT_example.py", "compliance/doc.txt"]
    first = build_test_results("pkg-1", file_names)
    second = build_test_results("pkg-1", file_names)
    assert first == second
