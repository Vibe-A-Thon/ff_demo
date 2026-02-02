"""Portable Evolution Pack (PEP) packaging service."""

from __future__ import annotations

import io
import json
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.config import APP_VERSION, PEP_STORAGE_DIR
from app.db import db
from app.services.capsules.amc.amc_service import (
    export_amc,
    build_prompt_manifest_yaml,
    build_tool_registry_yaml,
    validate_amc_bytes,
    preview_amc_bytes,
    save_amc_package,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "amc" / "schemas"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _build_transfer_manifest(team_ids: List[str], env_tag: str) -> Dict[str, Any]:
    return {
        "pack_id": f"pep-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "fraud_forge_app_version": APP_VERSION,
        "runtime_version": "1.0.0",
        "schema_versions": {
            "amc_schema": "1.0",
            "rsb_schema": "1.0",
            "brc_schema": "1.0",
        },
        "teams": team_ids,
        "env_tag": env_tag,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_contracts(team_id: str) -> Dict[str, bytes]:
    prompt_manifest = build_prompt_manifest_yaml(team_id)
    tool_registry = build_tool_registry_yaml()
    files: Dict[str, bytes] = {
        "contracts/prompt_manifest.yaml": prompt_manifest.encode("utf-8"),
        "contracts/tool_registry.yaml": tool_registry.encode("utf-8"),
    }
    
    # AMC Schemas
    for schema_file in ["amc_schema.json", "agent_profile_schema.json", "memory_schema.json"]:
        schema_path = SCHEMA_DIR / schema_file
        if schema_path.exists():
            files[f"contracts/schemas/{schema_file}"] = schema_path.read_bytes()

    # RSB Schema
    rsb_path = Path(__file__).resolve().parent.parent / "rsb" / "schemas" / "rsb_schema.json"
    if rsb_path.exists():
        files["contracts/schemas/rsb_schema.json"] = rsb_path.read_bytes()

    # BRC Schema
    brc_path = Path(__file__).resolve().parent.parent / "brc" / "schemas" / "brc_schema.json"
    if brc_path.exists():
        files["contracts/schemas/brc_schema.json"] = brc_path.read_bytes()

    return files


def _compute_pack_hash(files: Dict[str, bytes]) -> str:
    hashes = {path: f"sha256:{_sha256_bytes(content)}" for path, content in files.items()}
    return f"sha256:{_sha256_bytes(json.dumps(hashes, sort_keys=True).encode('utf-8'))}"


def validate_pep_bytes(payload: bytes) -> Dict[str, Any]:
    errors: List[str] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = zf.namelist()
        required = ["governance/TRANSFER_MANIFEST.json", "contracts/tool_registry.yaml", "contracts/prompt_manifest.yaml"]
        for name in required:
            if name not in names:
                errors.append(f"Missing required file: {name}")
        if not any(name.startswith("capsules/") and name.endswith(".amc") for name in names):
            errors.append("No AMC capsules found in PEP")
    return {"valid": len(errors) == 0, "errors": errors}


def preview_pep_bytes(payload: bytes) -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = zf.namelist()
        capsules = [name for name in names if name.startswith("capsules/") and name.endswith(".amc")]
        manifest = None
        try:
            with zf.open("governance/TRANSFER_MANIFEST.json") as handle:
                manifest = json.loads(handle.read().decode("utf-8"))
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            manifest = None
        return {
            "manifest": manifest,
            "capsules": capsules,
            "contracts": [name for name in names if name.startswith("contracts/")],
        }


async def export_pep_pack(
    team_ids: List[str], 
    env_tag: str, 
    include_eval_suite: bool, 
    include_model_bundle: bool,
    rsb_ids: List[str] = None,
    brc_ids: List[str] = None
) -> Tuple[bytes, Dict[str, Any], str]:
    files: Dict[str, bytes] = {}
    rsb_ids = rsb_ids or []
    brc_ids = brc_ids or []

    for team_id in team_ids:
        amc_payload, amc_manifest, amc_filename = await export_amc(team_id, {
            "include_memory_layers": ["semantic", "episodic", "procedural", "distilled"],
            "include_logs": "sanitized_only",
            "include_models": include_model_bundle,
            "include_battle_refs": True,
            "time_window_days": 180,
        }, env_tag)
        files[f"capsules/{amc_filename}"] = amc_payload

    # Export RSBs
    if rsb_ids:
        cursor = db.rsb_packages.find({"id": {"$in": rsb_ids}})
        async for rsb_pkg in cursor:
            path = rsb_pkg.get("storage_path")
            if path and Path(path).exists():
                files[f"capsules/rsb/{rsb_pkg['id']}.rsb"] = Path(path).read_bytes()

    # Export BRCs
    if brc_ids:
        cursor = db.brc_packages.find({"id": {"$in": brc_ids}})
        async for brc_pkg in cursor:
            path = brc_pkg.get("storage_path")
            if path and Path(path).exists():
                files[f"capsules/brc/{brc_pkg['id']}.brc"] = Path(path).read_bytes()

    contracts = _build_contracts(team_ids[0] if team_ids else "global")
    files.update(contracts)

    manifest = _build_transfer_manifest(team_ids, env_tag)
    manifest["rsb_count"] = len(rsb_ids)
    manifest["brc_count"] = len(brc_ids)
    manifest["pack_hash"] = _compute_pack_hash(files)
    files["governance/TRANSFER_MANIFEST.json"] = json.dumps(manifest, indent=2).encode("utf-8")

    if include_eval_suite:
        files["validation/synthetic_eval_suite/expected_metrics.yaml"] = (
            "metrics:\n  detection_rate: 0.9\n  false_positive_rate: 0.02\n"
        ).encode("utf-8")
        files["validation/synthetic_eval_suite/cases.jsonl"] = (
            "{\"case_id\":\"demo-001\",\"scenario\":\"synthetic\"}\n"
        ).encode("utf-8")

    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        buffer.seek(0)
        filename = f"FF_PORTABLE_EVOLUTION_PACK_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{env_tag}.pep.zip"
        return buffer.read(), manifest, filename


async def save_pep_pack(payload: bytes, manifest: Dict[str, Any], created_by: str, source: str = "export") -> Dict[str, Any]:
    pack_id = hashlib.sha256(payload).hexdigest()[:16]
    storage_path = PEP_STORAGE_DIR / f"{pack_id}.pep.zip"
    storage_path.write_bytes(payload)
    record = {
        "id": pack_id,
        "teams": manifest.get("teams", []),
        "env_tag": manifest.get("env_tag", "sandbox"),
        "manifest": manifest,
        "storage_path": str(storage_path),
        "source": source,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.pep_packs.insert_one(record)
    return record


async def import_pep_bytes(payload: bytes, created_by: str) -> Dict[str, Any]:
    report = validate_pep_bytes(payload)
    if not report.get("valid"):
        raise ValueError("PEP validation failed")

    preview = preview_pep_bytes(payload)
    manifest = preview.get("manifest") or {}
    await save_pep_pack(payload, manifest, created_by, source="import")

    imported_capsules: List[Dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        for name in preview.get("capsules", []):
            with zf.open(name) as handle:
                amc_payload = handle.read()
            amc_validation = validate_amc_bytes(amc_payload)
            if not amc_validation.get("valid"):
                imported_capsules.append({"file": name, "status": "failed", "errors": amc_validation.get("errors")})
                continue
            amc_preview = preview_amc_bytes(amc_payload)
            amc_manifest = amc_preview.get("manifest") or {}
            record = await save_amc_package(
                amc_payload,
                amc_manifest,
                amc_manifest.get("export_scope", {}).get("env_tag", "sandbox"),
                "import",
                created_by,
                validation=amc_validation,
            )
            imported_capsules.append({
                "file": name,
                "status": "imported",
                "package": record,
                "preview": amc_preview,
            })

    return {"manifest": manifest, "imports": imported_capsules}
