
import json
import zipfile
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from app.rsb_utils import read_zip_json, read_zip_text, compute_zip_hashes, verify_pack_hashes, scan_prohibited_content, find_first_match

SCHEMA_DIR = Path(__file__).parent / "schemas"

def validate_rsb_structure(zf: zipfile.ZipFile, file_names: List[str]) -> Dict[str, Any]:
    errors = []
    warnings = []
    
    required_files = [
        "manifest.json",
        "rule/specification.json",
        "rule/description.md",
        "rule/rule.json",
        "rule/rule_Patch.py",
    ]
    for req in required_files:
        if req not in file_names:
            errors.append(f"Missing required file: {req}")
            
    code_file = find_first_match(file_names, "code/ruleC_", ".py")
    if not code_file:
        errors.append("Missing core rule implementation (code/ruleC_*.py)")
        
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

def validate_schemas(manifest: Dict, rule_def: Dict) -> List[str]:
    errors = []
    if not HAS_JSONSCHEMA:
        return errors # Skip if lib missing

    def _validate(instance, schema_name):
        schema_path = SCHEMA_DIR / schema_name
        if not schema_path.exists():
            return
        try:
            schema = json.loads(schema_path.read_text())
            jsonschema.validate(instance=instance, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation failed for {schema_name}: {e.message}")
        except Exception as e:
            errors.append(f"Schema validation error {schema_name}: {str(e)}")

    if manifest:
        _validate(manifest, "rsb_manifest_schema.json")
    if rule_def:
        _validate(rule_def, "rsb_rule_schema.json")
        
    return errors

def run_full_validation(zf: zipfile.ZipFile) -> Dict[str, Any]:
    file_names = [n for n in zf.namelist() if not n.endswith("/")]
    
    # 1. Structure
    struct_res = validate_rsb_structure(zf, file_names)
    errors = struct_res["errors"]
    warnings = struct_res["warnings"]
    
    # 2. Parse JSONs
    manifest = read_zip_json(zf, "manifest.json")
    rule_spec = read_zip_json(zf, "rule/specification.json")
    rule_def = read_zip_json(zf, "rule/rule.json")
    
    # 3. Schema Validation
    if manifest and rule_def:
        schema_errors = validate_schemas(manifest, rule_def)
        errors.extend(schema_errors)
    
    # 4. Consistency
    if manifest and rule_def:
        if manifest.get("rule_id") != rule_def.get("rule_id"):
            errors.append("Manifest rule_id mismatch with rule definition")
            
    # 5. Integrity (Hashes)
    pack_hashes = read_zip_json(zf, "pack_hashes.json")
    if pack_hashes:
        computed = compute_zip_hashes(zf, file_names)
        h_err, h_warn = verify_pack_hashes(pack_hashes, computed)
        errors.extend(h_err)
        warnings.extend(h_warn)
    else:
        warnings.append("Integrity check skipped (pack_hashes.json missing)")
        
    # 6. Policy Scan
    policy_violations = scan_prohibited_content(zf, file_names)
    errors.extend(policy_violations)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "details": {
            "files_checked": len(file_names),
            "schema_check": "passed" if not any("Schema" in e for e in errors) else "failed"
        }
    }
