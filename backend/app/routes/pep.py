"""PEP packaging routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.models import PEPExportRequest
from app.security import require_permission
from app.services.capsules.pep.pep_service import (
    export_pep_pack,
    validate_pep_bytes,
    preview_pep_bytes,
    import_pep_bytes,
    save_pep_pack,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/pep/export")
async def export_pep(request: PEPExportRequest, current_user: dict = Depends(require_permission("pep:write"))):
    if not request.team_ids:
        raise HTTPException(status_code=400, detail="team_ids required")
    payload, manifest, filename = await export_pep_pack(
        request.team_ids,
        request.env_tag,
        request.include_eval_suite,
        request.include_model_bundle,
    )
    await save_pep_pack(payload, manifest, current_user.get("id", "unknown"))
    await record_audit(
        current_user.get("id", "unknown"),
        "pep.exported",
        "pep_pack",
        manifest.get("pack_id", filename),
        metadata={"teams": request.team_ids},
    )
    logger.info("pep.exported", extra={"payload": {"teams": request.team_ids}})
    response = Response(content=payload, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@router.post("/pep/validate")
async def validate_pep(file: UploadFile = File(...), current_user: dict = Depends(require_permission("pep:read"))):
    payload = await file.read()
    report = validate_pep_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "pep.validated",
        "pep_pack",
        "upload",
        metadata={"valid": report.get("valid")},
    )
    return report


@router.post("/pep/preview")
async def preview_pep(file: UploadFile = File(...), current_user: dict = Depends(require_permission("pep:read"))):
    payload = await file.read()
    preview = preview_pep_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "pep.previewed",
        "pep_pack",
        file.filename or "upload",
    )
    return preview


@router.post("/pep/import")
async def import_pep(file: UploadFile = File(...), current_user: dict = Depends(require_permission("pep:write"))):
    payload = await file.read()
    try:
        result = await import_pep_bytes(payload, current_user.get("id", "unknown"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await record_audit(
        current_user.get("id", "unknown"),
        "pep.imported",
        "pep_pack",
        result.get("manifest", {}).get("pack_id", "import"),
    )
    return result
