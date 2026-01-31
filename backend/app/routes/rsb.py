import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.config import RSB_STORAGE_DIR
from app.db import db
from app.models import RSBPackage, RSBPackageCreate
from app.rsb_utils import (
    build_rsb_tree,
    read_zip_json,
    read_zip_text,
    find_first_match,
    validate_rsb_payload,
    build_test_results,
)

router = APIRouter()

@router.get("/rsb-packages")
async def get_rsb_packages():
    packages = await db.rsb_packages.find({}, {"_id": 0}).to_list(100)
    return packages

@router.get("/rsb-packages/{package_id}")
async def get_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    return package

@router.post("/rsb-packages")
async def create_rsb_package(package_data: RSBPackageCreate):
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
    return package

@router.post("/rsb-packages/upload")
async def upload_rsb_package(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    compliance_badges: Optional[str] = Form(None),
):
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
            return package
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Invalid ZIP archive") from exc

@router.post("/rsb-packages/{package_id}/test")
async def test_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    test_results = package.get("test_results")
    if not test_results:
        file_names = package.get("manifest", {}).get("files_flat", [])
        test_results = build_test_results(package_id, file_names)

    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"test_results": test_results, "status": "tested"}})
    return test_results

@router.post("/rsb-packages/{package_id}/merge")
async def merge_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    if package.get("conflicts") and not package.get("conflict_resolutions"):
        raise HTTPException(status_code=409, detail="Merge conflicts must be resolved before merging")
    if package.get("validation", {}).get("valid") is False:
        raise HTTPException(status_code=400, detail="Package validation failed; fix errors before merge")

    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"status": "merged"}})
    return {"message": "Package merged successfully", "status": "merged"}

@router.post("/rsb-packages/{package_id}/resolve-conflicts")
async def resolve_rsb_conflicts(package_id: str, decisions: Dict[str, Any]):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")

    await db.rsb_packages.update_one(
        {"id": package_id},
        {"$set": {"conflict_resolutions": decisions}},
    )
    return await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})

@router.post("/rsb-packages/{package_id}/stage")
async def stage_rsb_package(package_id: str):
    package = await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    await db.rsb_packages.update_one({"id": package_id}, {"$set": {"status": "staged"}})
    return await db.rsb_packages.find_one({"id": package_id}, {"_id": 0})

@router.get("/rsb-packages/{package_id}/export")
async def export_rsb_package(package_id: str):
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
async def delete_rsb_package(package_id: str):
    result = await db.rsb_packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="RSB Package not found")
    return {"message": "RSB Package deleted"}
