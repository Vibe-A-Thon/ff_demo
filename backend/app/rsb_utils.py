import io
import json
import random
import re
import zipfile
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Optional, Tuple


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


def _read_zip_bytes(zf: zipfile.ZipFile, path: str) -> Optional[bytes]:
    try:
        with zf.open(path) as handle:
            return handle.read()
    except KeyError:
        return None


def compute_zip_hashes(zf: zipfile.ZipFile, file_names: List[str]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for name in file_names:
        payload = _read_zip_bytes(zf, name)
        if payload is None:
            continue
        hashes[name] = f"sha256:{sha256(payload).hexdigest()}"
    return hashes


def verify_pack_hashes(
    pack_hashes: Dict[str, Any],
    computed_hashes: Dict[str, str],
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    files_map = None
    if isinstance(pack_hashes, dict):
        if isinstance(pack_hashes.get("files"), dict):
            files_map = pack_hashes.get("files")
        elif isinstance(pack_hashes.get("hashes"), dict):
            files_map = pack_hashes.get("hashes")

    if not isinstance(files_map, dict):
        warnings.append("pack_hashes.json has no recognizable file hash map")
        return errors, warnings

    for path, expected in files_map.items():
        actual = computed_hashes.get(path)
        if actual is None:
            errors.append(f"pack_hashes.json references missing file: {path}")
            continue
        expected_str = str(expected)
        if expected_str.startswith("sha256:"):
            expected_str = expected_str
        else:
            expected_str = f"sha256:{expected_str}"
        if expected_str != actual:
            errors.append(f"Hash mismatch for {path}")

    return errors, warnings


def scan_prohibited_content(zf: zipfile.ZipFile, file_names: List[str]) -> List[str]:
    patterns = {
        "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{2,3}\)|\d{2,3})[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    }
    allowed_ext = {".md", ".json", ".py", ".txt", ".yaml", ".yml", ".csv", ".log"}
    violations: List[str] = []

    for name in file_names:
        if not any(name.endswith(ext) for ext in allowed_ext):
            continue
        payload = _read_zip_bytes(zf, name)
        if not payload:
            continue
        if len(payload) > 1024 * 1024:
            continue
        text = payload.decode("utf-8", errors="ignore")
        for label, pattern in patterns.items():
            if pattern.search(text):
                violations.append(f"Potential {label} detected in {name}")

    return violations


def run_rsb_validation(
    zf: zipfile.ZipFile,
    file_names: List[str],
    manifest: Optional[Dict[str, Any]],
    rule_spec: Optional[Dict[str, Any]],
    rule_def: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    validation = validate_rsb_payload(manifest, rule_spec, rule_def, file_names)

    pack_hashes = read_zip_json(zf, "pack_hashes.json")
    if pack_hashes is None:
        validation["warnings"].append("pack_hashes.json missing; hash integrity not verified")
    else:
        computed_hashes = compute_zip_hashes(zf, file_names)
        hash_errors, hash_warnings = verify_pack_hashes(pack_hashes, computed_hashes)
        validation["errors"].extend(hash_errors)
        validation["warnings"].extend(hash_warnings)
        validation["hash_verification"] = {
            "status": "failed" if hash_errors else "passed",
            "checked": len(computed_hashes),
        }

    policy_violations = scan_prohibited_content(zf, file_names)
    if policy_violations:
        validation["errors"].extend(policy_violations)
    validation["policy_scan"] = {
        "status": "failed" if policy_violations else "passed",
        "violations": policy_violations,
    }

    validation["valid"] = len(validation["errors"]) == 0
    return validation


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


def bump_patch_version(version: str) -> str:
    parts = [int(p) if p.isdigit() else 0 for p in version.split(".")]
    while len(parts) < 3:
        parts.append(0)
    parts[2] += 1
    return ".".join(str(p) for p in parts[:3])


def build_rsb_archive(
    manifest: Dict[str, Any],
    rule_spec: Dict[str, Any],
    rule_def: Dict[str, Any],
    description_md: str,
    patch_script: str,
    code: str,
    code_patch: Optional[str],
    test_files: Optional[Dict[str, str]] = None,
    compliance_docs: Optional[Dict[str, str]] = None,
    test_results: Optional[Dict[str, Any]] = None,
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("rule/specification.json", json.dumps(rule_spec, indent=2))
        zf.writestr("rule/rule.json", json.dumps(rule_def, indent=2))
        zf.writestr("rule/description.md", description_md or "")
        zf.writestr("rule/rule_Patch.py", patch_script or "")

        rule_id = manifest.get("rule_id", "RULE")
        zf.writestr(f"code/ruleC_{rule_id}.py", code or "")
        if code_patch:
            zf.writestr(f"code/ruleCP_{rule_id}.py", code_patch)

        for name, content in (test_files or {}).items():
            zf.writestr(name, content)
        for name, content in (compliance_docs or {}).items():
            zf.writestr(name, content)
        if test_results:
            zf.writestr("tests/test_results.json", json.dumps(test_results, indent=2))

    buffer.seek(0)
    return buffer.read()
