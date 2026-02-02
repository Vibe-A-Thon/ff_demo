"""BRC capsule export/import/validation utilities."""

from __future__ import annotations

import io
import json
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import validate as jsonschema_validate
from jsonschema import ValidationError

from app.config import APP_VERSION, BRC_STORAGE_DIR
from app.db import db
from app.rag_utils import contains_sensitive_identifiers

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_schema(name: str) -> Dict[str, Any]:
    schema_path = SCHEMA_DIR / name
    if not schema_path.exists():
        return {}
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _safe_members(zip_file: zipfile.ZipFile) -> List[str]:
    safe_names: List[str] = []
    for member in zip_file.namelist():
        if member.startswith("/") or ".." in member.split("/"):
            raise ValueError("Unsafe path detected in BRC archive")
        safe_names.append(member)
    return safe_names


def _compute_pack_hashes(files: Dict[str, bytes]) -> Tuple[Dict[str, str], str]:
    hashes: Dict[str, str] = {}
    for path, content in files.items():
        if path == "pack_hashes.json":
            continue
        hashes[path] = f"sha256:{_sha256_bytes(content)}"
    pack_hash = _sha256_bytes(json.dumps(hashes, sort_keys=True).encode("utf-8"))
    return hashes, f"sha256:{pack_hash}"


def _build_summary(run: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# Battle Run Summary",
            "",
            f"- Run ID: {run.get('id')}",
            f"- Scenario: {run.get('scenario_id')}",
            f"- Mode: {run.get('mode')}",
            f"- Events: {len(events)}",
            "",
            "This capsule contains sanitized, synthetic-only outputs.",
        ]
    )


def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload_text = json.dumps(payload, default=str)
    if contains_sensitive_identifiers(payload_text):
        return {"note": "redacted", "reason": "sensitive identifiers detected"}
    return payload


def _stage_folder(stage: str | None, default: str = "00_prepare") -> str:
    if not stage:
        return default
    if stage.isdigit():
        return f"{stage.zfill(2)}_stage"
    return stage


def _build_stage_outputs(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    stage_outputs: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
            continue
        payload = _sanitize_payload(event.get("payload", {}))
        stage = payload.get("stage") or event.get("payload", {}).get("stage") or "00_prepare"
        stage_key = _stage_folder(str(stage))
        stage_outputs.setdefault(stage_key, []).append(payload)
    return stage_outputs


def _extract_red_simulation(events: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for event in events:
        if event.get("event_type") != "agent.output":
            continue
        payload = event.get("payload", {})
        if str(payload.get("team", "")).lower() == "red":
            red_outputs = payload.get("outputs", {})
            return {
                "team": payload.get("team"),
                "agent": payload.get("agent"),
                "simulate_transactions": red_outputs.get("simulate_transactions", {}),
                "apply_attack": red_outputs.get("apply_attack", {}),
                "attack_plan": red_outputs.get("attack_plan", {}),
            }
    return None


def build_brc_archive(run: Dict[str, Any], events: List[Dict[str, Any]]) -> Tuple[bytes, Dict[str, Any], str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    battle_type = run.get("scenario_id", "battle")
    archive_name = f"{battle_type}_{run.get('id')}_{timestamp}.brc"

    files: Dict[str, bytes] = {}
    stage_outputs = _build_stage_outputs(events)

    red_simulation = _extract_red_simulation(events)
    if red_simulation:
        files["inputs/red_simulation_data.json"] = json.dumps(red_simulation, indent=2, default=str).encode("utf-8")

    files["orchestrator/run_summary.md"] = _build_summary(run, events).encode("utf-8")

    for stage_key, payloads in stage_outputs.items():
        for idx, payload in enumerate(payloads, start=1):
            team = str(payload.get("team", "system")).lower() or "system"
            file_name = f"stages/{stage_key}/{team}_output_{idx:02d}.json"
            files[file_name] = json.dumps(payload, indent=2, default=str).encode("utf-8")

    manifest = {
        "battle_type": battle_type,
        "run_id": run.get("id"),
        "exported_at": timestamp,
        "event_count": len(events),
        "artifacts": sorted(files.keys()),
    }

    schema = _load_schema("brc_schema.json")
    if schema:
        jsonschema_validate(instance=manifest, schema=schema)

    files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")
    metadata = {
        "battle_type": battle_type,
        "run_id": run.get("id"),
        "seed": run.get("seed"),
        "mode": run.get("mode"),
        "current_stage": run.get("current_stage"),
        "step_count": run.get("step_count"),
        "exported_at": timestamp,
        "schema_version": "1.2",
        "app_version": APP_VERSION,
    }
    files["metadata.json"] = json.dumps(metadata, indent=2, default=str).encode("utf-8")

    hashes, pack_hash = _compute_pack_hashes(files)
    files["pack_hashes.json"] = json.dumps({"hash_algo": "sha256", "files": hashes, "pack_hash": pack_hash}, indent=2).encode("utf-8")

    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, content in files.items():
                archive.writestr(path, content)
        buffer.seek(0)
        return buffer.read(), manifest, archive_name


def validate_brc_bytes(payload: bytes) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = _safe_members(archive)
        required = ["manifest.json", "metadata.json", "pack_hashes.json"]
        for name in required:
            if name not in names:
                errors.append(f"Missing required file: {name}")

        manifest = None
        if "manifest.json" in names:
            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except json.JSONDecodeError:
                errors.append("manifest.json invalid JSON")

        schema = _load_schema("brc_schema.json")
        if manifest and schema:
            try:
                jsonschema_validate(instance=manifest, schema=schema)
            except ValidationError as exc:
                errors.append(f"manifest schema error: {exc.message}")

        try:
            pack_hashes = json.loads(archive.read("pack_hashes.json").decode("utf-8"))
        except (KeyError, json.JSONDecodeError):
            pack_hashes = None
            errors.append("pack_hashes.json missing or invalid")

        if pack_hashes:
            file_hashes = pack_hashes.get("files", {})
            for path, expected in file_hashes.items():
                if path not in names:
                    errors.append(f"Missing file listed in pack_hashes.json: {path}")
                    continue
                actual = f"sha256:{_sha256_bytes(archive.read(path))}"
                if actual != expected:
                    errors.append(f"Hash mismatch for {path}")

            computed_pack_hash = _sha256_bytes(json.dumps(file_hashes, sort_keys=True).encode("utf-8"))
            if pack_hashes.get("pack_hash") and pack_hashes.get("pack_hash") != f"sha256:{computed_pack_hash}":
                warnings.append("Pack hash mismatch")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def preview_brc_bytes(payload: bytes) -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        manifest = None
        if "manifest.json" in names:
            try:
                manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            except json.JSONDecodeError:
                manifest = None
        stage_files = [name for name in names if name.startswith("stages/") and name.endswith(".json")]
        stage_summary: Dict[str, int] = {}
        for name in stage_files:
            parts = name.split("/")
            if len(parts) < 3:
                continue
            stage_key = parts[1]
            stage_summary[stage_key] = stage_summary.get(stage_key, 0) + 1
        return {
            "manifest": manifest,
            "stage_files": stage_files,
            "stage_summary": stage_summary,
            "artifact_count": len(names),
        }


def import_brc_bytes(payload: bytes) -> Dict[str, Any]:
    report = validate_brc_bytes(payload)
    if not report.get("valid"):
        raise ValueError("BRC validation failed")

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        battle_type = manifest.get("battle_type", "Imported Battle")
        run_id = manifest.get("run_id", "imported")
        stage_turns = _build_stage_turns(archive)

    return {
        "manifest": manifest,
        "battle_type": battle_type,
        "run_id": run_id,
        "turns": stage_turns,
    }


def _derive_action(payload: Dict[str, Any] | None, team: str) -> str:
    if not payload:
        return "N/A"
    outputs = payload.get("outputs") or {}
    if team == "red":
        return (
            outputs.get("attack_plan", {}).get("campaign")
            or outputs.get("apply_attack", {}).get("strategy")
            or outputs.get("simulate_transactions", {}).get("name")
            or payload.get("action")
            or "simulated"
        )
    return (
        outputs.get("decision", {}).get("outcome")
        or outputs.get("mitigation", {}).get("plan")
        or payload.get("action")
        or "review"
    )


def _detect_team(payload: Dict[str, Any], filename: str) -> str | None:
    team = str(payload.get("team", "")).lower()
    if team in {"red", "blue"}:
        return team
    if "red" in filename.lower():
        return "red"
    if "blue" in filename.lower():
        return "blue"
    return None


def _build_stage_turns(archive: zipfile.ZipFile) -> List[Dict[str, Any]]:
    stage_payloads: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for name in archive.namelist():
        if not (name.startswith("stages/") and name.endswith(".json")):
            continue
        parts = name.split("/")
        if len(parts) < 3:
            continue
        stage_key = parts[1]
        if name.endswith("orchestrator_output.json"):
            continue
        try:
            payload = json.loads(archive.read(name).decode("utf-8"))
        except json.JSONDecodeError:
            continue
        team = _detect_team(payload, name)
        if team not in {"red", "blue"}:
            continue
        stage_payloads.setdefault(stage_key, {})[team] = payload

    turns: List[Dict[str, Any]] = []
    for stage_key in sorted(stage_payloads.keys()):
        red_payload = stage_payloads[stage_key].get("red")
        blue_payload = stage_payloads[stage_key].get("blue")
        turns.append(
            {
                "stage": stage_key,
                "red_team": {
                    "action": _derive_action(red_payload, "red"),
                    "success": (red_payload or {}).get("success", True),
                },
                "blue_team": {
                    "action": _derive_action(blue_payload, "blue"),
                    "blocked": (blue_payload or {}).get("blocked", True),
                },
                "stage_outputs": {"red": red_payload, "blue": blue_payload},
            }
        )
    return turns


def save_brc_package(payload: bytes, manifest: Dict[str, Any], created_by: str, status: str = "exported") -> Dict[str, Any]:
    package_id = hashlib.sha256(payload).hexdigest()[:16]
    storage_path = BRC_STORAGE_DIR / f"{package_id}.brc"
    storage_path.write_bytes(payload)
    record = {
        "id": package_id,
        "run_id": manifest.get("run_id"),
        "battle_type": manifest.get("battle_type"),
        "status": status,
        "manifest": manifest,
        "storage_path": str(storage_path),
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return record


async def persist_brc_package(payload: bytes, manifest: Dict[str, Any], created_by: str, status: str = "exported") -> Dict[str, Any]:
    record = save_brc_package(payload, manifest, created_by, status)
    await db.brc_packages.insert_one(record)
    return record
