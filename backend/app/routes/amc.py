"""AMC capsule routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.models import AMCExportRequest, AMCImportRequest
from app.security import require_permission
from app.services.capsules.amc.amc_service import (
    export_amc,
    validate_amc_bytes,
    preview_amc_bytes,
    diff_amc_bytes,
    save_amc_package,
    list_catalog,
    activate_package,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/amc/export")
async def export_amc_capsule(
    request: AMCExportRequest,
    current_user: dict = Depends(require_permission("amc:write")),
):
    """Export an AMC capsule for a team."""
    try:
        payload, manifest, filename = await export_amc(
            request.team_id,
            request.export_scope.model_dump(),
            request.env_tag,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await save_amc_package(payload, manifest, request.env_tag, "export", current_user.get("id", "unknown"))
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.exported",
        "amc_package",
        manifest.get("team_id", request.team_id),
        metadata={"team_id": request.team_id},
    )
    logger.info("amc.exported", extra={"payload": {"team_id": request.team_id}})
    response = Response(content=payload, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.post("/amc/validate")
async def validate_amc_capsule(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("amc:read")),
):
    """Validate an AMC capsule."""
    payload = await file.read()
    report = validate_amc_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.validated",
        "amc_package",
        file.filename or "upload",
        metadata={"valid": report.get("valid")},
    )
    return report


@router.post("/amc/preview")
async def preview_amc_capsule(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("amc:read")),
):
    """Preview an AMC capsule."""
    payload = await file.read()
    preview = preview_amc_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.previewed",
        "amc_package",
        file.filename or "upload",
    )
    return preview


@router.post("/amc/import")
async def import_amc_capsule(
    mode: str = Form("merge"),
    activate: bool = Form(False),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("amc:approve")),
):
    """Import an AMC capsule."""
    payload = await file.read()
    validation = validate_amc_bytes(payload)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail="AMC validation failed", headers={"X-AMC-Errors": ";".join(validation.get("errors", []))})

    preview = preview_amc_bytes(payload)
    manifest = preview.get("manifest") or {}
    record = await save_amc_package(
        payload,
        manifest,
        manifest.get("export_scope", {}).get("env_tag", "sandbox"),
        "import",
        current_user.get("id", "unknown"),
        validation=validation,
    )

    package_id = record.get("id") or "unknown"
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.imported",
        "amc_package",
        package_id,
        metadata={"mode": mode, "team_id": record.get("team_id")},
    )
    if activate and package_id != "unknown":
        await activate_package(package_id, current_user.get("id", "unknown"))
    return {"package": record, "preview": preview}


@router.post("/amc/diff")
async def diff_amc_capsules(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("amc:read")),
):
    """Diff two AMC capsules."""
    old_payload = await old_file.read()
    new_payload = await new_file.read()
    diff = diff_amc_bytes(old_payload, new_payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.diffed",
        "amc_package",
        "diff",
        metadata={"old": old_file.filename, "new": new_file.filename},
    )
    return diff


@router.get("/amc/catalog")
async def catalog_amc_capsules(
    current_user: dict = Depends(require_permission("amc:read")),
):
    """List AMC catalog entries."""
    await record_audit(
        current_user.get("id", "unknown"),
        "amc.catalog",
        "amc_package",
        "catalog",
    )
    return await list_catalog()


@router.post("/amc/activate")
async def activate_amc_capsule(
    package_id: str = Form(...),
    current_user: dict = Depends(require_permission("amc:approve")),
):
    """Activate an imported AMC package in sandbox."""
    try:
        package = await activate_package(package_id, current_user.get("id", "unknown"))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await record_audit(
        current_user.get("id", "unknown"),
        "amc.activated",
        "amc_package",
        package_id,
        metadata={"team_id": package.get("team_id")},
    )
    return {"message": "AMC activated", "package": package}
