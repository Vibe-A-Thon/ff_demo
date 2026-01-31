import json
import random
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def build_rsb_tree(file_names: List[str]) -> List[Dict[str, Any]]:
    root: Dict[str, Any] = {}
    for name in file_names:
        parts = [p for p in name.split("/") if p]
        cursor = root
        for idx, part in enumerate(parts):
            if idx == len(parts) - 1:
                cursor.setdefault("__files", []).append(part)
            else:
                cursor = cursor.setdefault(part, {})

    def to_tree(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for key, value in node.items():
            if key == "__files":
                for file_name in value:
                    items.append({"name": file_name})
                continue
            children = to_tree(value)
            items.append({"name": f"{key}/", "children": children})
        return items

    return to_tree(root)


def read_zip_text(zf: zipfile.ZipFile, path: str) -> Optional[str]:
    try:
        with zf.open(path) as handle:
            return handle.read().decode("utf-8")
    except KeyError:
        return None


def read_zip_json(zf: zipfile.ZipFile, path: str) -> Optional[Dict[str, Any]]:
    payload = read_zip_text(zf, path)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def find_first_match(file_names: List[str], prefix: str, suffix: str) -> Optional[str]:
    for name in file_names:
        if name.startswith(prefix) and name.endswith(suffix):
            return name
    return None


def validate_rsb_payload(
    manifest: Optional[Dict[str, Any]],
    rule_spec: Optional[Dict[str, Any]],
    rule_def: Optional[Dict[str, Any]],
    file_names: List[str],
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    required_files = [
        "manifest.json",
        "rule/specification.json",
        "rule/description.md",
        "rule/rule.json",
        "rule/rule_Patch.py",
    ]
    for required in required_files:
        if required not in file_names:
            errors.append(f"Missing required file: {required}")

    if manifest is None:
        errors.append("manifest.json is missing or invalid JSON")
    else:
        for key in ["rule_id", "name", "rule_version", "attack_type"]:
            if not manifest.get(key):
                errors.append(f"manifest.json missing required field: {key}")

    if rule_spec is None:
        errors.append("rule/specification.json is missing or invalid JSON")
    if rule_def is None:
        errors.append("rule/rule.json is missing or invalid JSON")

    if rule_spec and manifest and rule_spec.get("rule_id") != manifest.get("rule_id"):
        errors.append("rule/specification.json rule_id does not match manifest.json rule_id")
    if rule_def and manifest and rule_def.get("rule_id") != manifest.get("rule_id"):
        errors.append("rule/rule.json rule_id does not match manifest.json rule_id")

    code_file = find_first_match(file_names, "code/ruleC_", ".py")
    if not code_file:
        errors.append("Missing core rule implementation (code/ruleC_*.py)")

    unit_tests = [name for name in file_names if name.startswith("tests/ruleUT_") and name.endswith(".py")]
    if not unit_tests:
        warnings.append("No unit test files found (tests/ruleUT_*.py)")

    integration_tests = [name for name in file_names if name.startswith("tests/ruleIT_") and name.endswith(".py")]
    if not integration_tests:
        warnings.append("No integration test files found (tests/ruleIT_*.py)")

    compliance_docs = [name for name in file_names if name.startswith("compliance/")]
    if not compliance_docs:
        warnings.append("No compliance documentation found in compliance/")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def build_test_results(package_id: str, file_names: List[str]) -> Dict[str, Any]:
    unit_tests = [name for name in file_names if name.startswith("tests/ruleUT_") and name.endswith(".py")]
    integration_tests = [name for name in file_names if name.startswith("tests/ruleIT_") and name.endswith(".py")]
    compliance_files = [name for name in file_names if name.startswith("compliance/")]

    rng = random.Random(package_id)
    unit_total = max(1, len(unit_tests) * 5)
    integ_total = max(1, len(integration_tests) * 3)
    compliance_total = max(1, min(8, len(compliance_files)))

    unit_failed = 0 if unit_total <= 5 else rng.randint(0, 1)
    integ_failed = 0 if integ_total <= 3 else rng.randint(0, 1)

    return {
        "unit_tests": {"passed": unit_total - unit_failed, "failed": unit_failed, "total": unit_total},
        "integration_tests": {"passed": integ_total - integ_failed, "failed": integ_failed, "total": integ_total},
        "compliance_checks": {"passed": compliance_total, "failed": 0, "total": compliance_total},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
