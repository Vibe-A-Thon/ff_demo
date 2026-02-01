"""RSB package routes."""

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from app.config import RSB_STORAGE_DIR
from app.core.external_services import DatabaseClient
from app.deps import get_db
from app.models import RSBPackage, RSBPackageCreate
from app.security import require_permission
from app.rsb_utils import (
    build_rsb_tree,
    read_zip_json,
    read_zip_text,
    find_first_match,
    validate_rsb_payload,
    build_test_results,
    bump_patch_version,
    build_rsb_archive,
)
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/rsb-packages")
async def get_rsb_packages(
    current_user: dict = Depends(require_permission("rsb:read")),
    db: DatabaseClient = Depends(get_db),
) -> List[Dict[str, Any]]:
    packages = await db.rsb_packages.find({}, {"_id": 0}).to_list(100)
    return packages

@router.get("/rsb-packages/{package_id}")
async def get_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    return package

@router.post("/rsb-packages")
async def create_rsb_package(
    package_data: RSBPackageCreate,
    current_user: dict = Depends(require_permission("rsb:write")),
    db: DatabaseClient = Depends(get_db),
) -> RSBPackage:
    package = RSBPackage(**package_data.model_dump())
    rule_id = package.rule_id or package.manifest.get("rule_id")
    if rule_id:
        conflicts = await db.rsb_packages.find({"rule_id": rule_id}, {"_id": 0}).to_list(5)
        package.conflicts = [
            {
                "id": f"conflict-{conflict.get('id')}",
                "type": "rule_id_collision",
                "rule_id": rule_id,
                "existing_package_id": conflict.get("id"),
                "existing_version": conflict.get("version"),
            }
            for conflict in conflicts
        ]
    await db.rsb_packages.insert_one(package.model_dump())
    logger.info("rsb.package.created", extra={"payload": {"package_id": package.id, "rule_id": package.rule_id}})
    return package

@router.post("/rsb-packages/upload")
async def upload_rsb_package(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    compliance_badges: Optional[str] = Form(None),
    current_user: dict = Depends(require_permission("rsb:write")),
    db: DatabaseClient = Depends(get_db),
) -> RSBPackage:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if not file.filename.lower().endswith((".rsb", ".zip")):
        raise HTTPException(status_code=400, detail="Invalid file type; expected .rsb")

    payload = await file.read()
    checksum = __import__("hashlib").sha256(payload).hexdigest()
    zip_io = io.BytesIO(payload)

    try:
        with zipfile.ZipFile(zip_io) as zf:
            file_names = [name for name in zf.namelist() if not name.endswith("/")]
            manifest = read_zip_json(zf, "manifest.json")
            rule_spec = read_zip_json(zf, "rule/specification.json")
            rule_def = read_zip_json(zf, "rule/rule.json")
            description_md = read_zip_text(zf, "rule/description.md")
            patch_script = read_zip_text(zf, "rule/rule_Patch.py")

            code_file = find_first_match(file_names, "code/ruleC_", ".py")
            code_patch_file = find_first_match(file_names, "code/ruleCP_", ".py")
            code = read_zip_text(zf, code_file) if code_file else None
            code_patch = read_zip_text(zf, code_patch_file) if code_patch_file else None

            test_results = read_zip_json(zf, "tests/test_results.json")
            if test_results is None:
                test_results_file = find_first_match(file_names, "testcases/", "_test_results.json")
                if test_results_file:
                    test_results = read_zip_json(zf, test_results_file)

            compliance_docs: List[Dict[str, Any]] = []
            for entry in file_names:
                if not entry.startswith("compliance/"):
                    continue
                content = read_zip_text(zf, entry)
                if content is None:
                    continue
                if entry.endswith(".json"):
                    parsed = None
                    try:
                        parsed = json.loads(content)
                    except json.JSONDecodeError:
                        parsed = None
                    compliance_docs.append({"name": entry, "type": "json", "content": parsed or content})
                else:
                    compliance_docs.append({"name": entry, "type": "text", "content": content})

            validation = validate_rsb_payload(manifest, rule_spec, rule_def, file_names)
            rule_id = None
            if manifest:
                rule_id = manifest.get("rule_id")
            if not rule_id and rule_spec:
                rule_id = rule_spec.get("rule_id")

            resolved_name = name or (manifest.get("name") if manifest else None) or file.filename
            resolved_version = version or (manifest.get("rule_version") if manifest else None) or "1.0.0"
            resolved_description = description or (rule_spec.get("description") if rule_spec else None) or ""

            badges: List[str] = []
            if compliance_badges:
                badges = [badge.strip() for badge in compliance_badges.split(",") if badge.strip()]
            if not badges and manifest and isinstance(manifest.get("compliance_badges"), list):
                badges = manifest.get("compliance_badges")

            manifest = manifest or {}
            manifest["files"] = build_rsb_tree(file_names)
            manifest["files_flat"] = file_names

            package = RSBPackage(
                name=resolved_name,
                version=resolved_version,
                description=resolved_description,
                manifest=manifest,
                rules=[rule_id] if rule_id else [],
                rule_id=rule_id,
                rule_spec=rule_spec,
                rule_definition=rule_def,
                description_md=description_md,
                code=code,
                code_patch=code_patch,
                patch_script=patch_script,
                files=manifest.get("files", []),
                test_files=[name for name in file_names if name.startswith("tests/")],
                testcases=[name for name in file_names if name.startswith("testcases/")],
                compliance_badges=badges,
                compliance_docs=compliance_docs,
                test_results=test_results,
                validation=validation,
                checksum=checksum,
                source_filename=file.filename,
                status="pending" if validation.get("valid") else "failed",
            )

            if rule_id:
                conflicts = await db.rsb_packages.find({"rule_id": rule_id}, {"_id": 0}).to_list(5)
                package.conflicts = [
                    {
                        "id": f"conflict-{conflict.get('id')}",
                        "type": "rule_id_collision",
                        "rule_id": rule_id,
                        "existing_package_id": conflict.get("id"),
                        "existing_version": conflict.get("version"),
                    }
                    for conflict in conflicts
                ]

            storage_path = RSB_STORAGE_DIR / f"{package.id}.rsb"
            storage_path.write_bytes(payload)
            package.storage_path = str(storage_path)

            await db.rsb_packages.insert_one(package.model_dump())
            logger.info(
                "rsb.package.uploaded",
                extra={"payload": {"package_id": package.id, "status": package.status, "file": file.filename}},
            )
            return package
    except zipfile.BadZipFile as exc:
        logger.exception("Invalid RSB archive", extra={"payload": {"filename": file.filename}})
        raise HTTPException(status_code=400, detail="Invalid ZIP archive") from exc

@router.post("/rsb-packages/{package_id}/test")
async def test_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:write")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    test_results = package.get("test_results")
    if not test_results:
        file_names = package.get("manifest", {}).get("files_flat", [])
        test_results = build_test_results(package_id, file_names)

    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"test_results": test_results, "status": "tested"}})
    logger.info("rsb.package.tested", extra={"payload": {"package_id": package_id, "status": "tested"}})
    return test_results


@router.get("/rsb-packages/{package_id}/diffs")
async def get_rsb_diffs(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    rule_id = package.get("rule_id") or (package.get("manifest") or {}).get("rule_id")
    diffs = []
    if package.get("rule_spec"):
        diffs.append(
            {
                "id": f"spec-{package_id}",
                "package_id": package_id,
                "name": f"{rule_id or 'RuleSpec'} Specification",
                "type": "rulespec",
                "oldCode": json.dumps(package.get("rule_spec"), indent=2),
                "newCode": json.dumps(package.get("rule_spec_patch") or package.get("rule_spec"), indent=2),
                "status": package.get("patch_decision", "pending"),
            }
        )

    if package.get("code"):
        diffs.append(
            {
                "id": f"code-{package_id}",
                "package_id": package_id,
                "name": f"{rule_id or 'Rule'} Code",
                "type": "code",
                "oldCode": package.get("code"),
                "newCode": package.get("code_patch") or package.get("code"),
                "status": package.get("patch_decision", "pending"),
            }
        )

    return {
        "package_id": package_id,
        "rule_id": rule_id,
        "version": package.get("version"),
        "status": package.get("status"),
        "conflicts": package.get("conflicts", []),
        "diffs": diffs,
    }


@router.post("/rsb-packages/{package_id}/apply-patch")
async def apply_rsb_patch(
    package_id: str,
    payload: Dict[str, Any],
    current_user: dict = Depends(require_permission("rsb:approve")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    decision = payload.get("decision", "accepted")
    conflict_resolutions = payload.get("conflict_resolutions") or {}
    commit_message = payload.get("commit_message") or ""

    patched_code = package.get("code_patch") if decision == "accepted" else package.get("code")
    rule_spec = package.get("rule_spec") or {}
    patched_spec = dict(rule_spec)
    if decision == "accepted":
        patched_spec["patch_notes"] = commit_message or "Patch applied via Visual Patcher"

    manifest = dict(package.get("manifest") or {})
    manifest["rule_version"] = bump_patch_version(package.get("version") or "1.0.0")
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()

    archive_bytes = build_rsb_archive(
        manifest=manifest,
        rule_spec=patched_spec,
        rule_def=package.get("rule_definition") or {},
        description_md=package.get("description_md") or "",
        patch_script=package.get("patch_script") or "",
        code=patched_code or "",
        code_patch=package.get("code_patch"),
        test_results=package.get("test_results"),
    )

    patched_path = RSB_STORAGE_DIR / f"{package_id}_patched.rsb"
    patched_path.write_bytes(archive_bytes)

    updates = {
        "status": "patched" if decision == "accepted" else "rejected",
        "patch_decision": decision,
        "patch_commit_message": commit_message,
        "patch_applied_at": datetime.now(timezone.utc).isoformat(),
        "conflict_resolutions": conflict_resolutions,
        "code": patched_code,
        "rule_spec_patch": patched_spec,
        "version": manifest.get("rule_version"),
        "storage_path": str(patched_path),
    }

    await db.rsb_packages.update_one({"id": package_id}, {"$set": updates})
    logger.info(
        "rsb.package.patched",
        extra={"payload": {"package_id": package_id, "decision": decision, "status": updates.get("status")}},
    )
    return await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})

@router.post("/rsb-packages/{package_id}/merge")
async def merge_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:approve")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    if package.get("conflicts") and not package.get("conflict_resolutions"):
        raise HTTPException(status_code=409, detail="Merge conflicts must be resolved before merging")
    if package.get("validation", {}).get("valid") is False:
        raise HTTPException(status_code=400, detail="Package validation failed; fix errors before merge")

    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"status": "merged"}})
    logger.info("rsb.package.merged", extra={"payload": {"package_id": package_id}})
    return {"message": "Package merged successfully", "status": "merged"}

@router.post("/rsb-packages/{package_id}/resolve-conflicts")
async def resolve_rsb_conflicts(
    package_id: str,
    decisions: Dict[str, Any],
    current_user: dict = Depends(require_permission("rsb:approve")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    await db.rsb_packages.update_one(
        {"id": package_id},
        {"$set": {"conflict_resolutions": decisions}},
    )
    logger.info("rsb.package.conflicts_resolved", extra={"payload": {"package_id": package_id}})
    return await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})

@router.post("/rsb-packages/{package_id}/stage")
async def stage_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:approve")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"status": "staged"}})
    logger.info("rsb.package.staged", extra={"payload": {"package_id": package_id}})
    return await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})

@router.get("/rsb-packages/{package_id}/export")
async def export_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:read")),
    db: DatabaseClient = Depends(get_db),
) -> StreamingResponse:
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    storage_path = package.get("storage_path")
    if storage_path and Path(storage_path).exists():
        file_path = Path(storage_path)
        response = StreamingResponse(file_path.open("rb"), media_type="application/zip")
        response.headers["Content-Disposition"] = f"attachment; filename={package.get('name','package')}.rsb"
        return response

    raise HTTPException(status_code=404, detail="RSB archive not available")

@router.delete("/rsb-packages/{package_id}")
async def delete_rsb_package(
    package_id: str,
    current_user: dict = Depends(require_permission("rsb:approve")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, str]:
    result = await db.rsb_packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    logger.info("rsb.package.deleted", extra={"payload": {"package_id": package_id}})
    return {"message": "RSB Package deleted"}
