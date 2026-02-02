"""BRC capsule routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.security import require_permission
from app.services.capsules.brc.brc_service import (
    validate_brc_bytes,
    preview_brc_bytes,
    import_brc_bytes,
    persist_brc_package,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post("/brc/validate")
async def validate_brc(file: UploadFile = File(...), current_user: dict = Depends(require_permission("battle:read"))):
    payload = await file.read()
    report = validate_brc_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.validated",
        "brc_package",
        file.filename or "upload",
        metadata={"valid": report.get("valid")},
    )
    return report


@router.post("/brc/preview")
async def preview_brc(file: UploadFile = File(...), current_user: dict = Depends(require_permission("battle:read"))):
    payload = await file.read()
    preview = preview_brc_bytes(payload)
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.previewed",
        "brc_package",
        file.filename or "upload",
    )
    return preview


@router.post("/brc/import")
async def import_brc(file: UploadFile = File(...), current_user: dict = Depends(require_permission("battle:write"))):
    payload = await file.read()
    try:
        result = import_brc_bytes(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await persist_brc_package(payload, result.get("manifest", {}), current_user.get("id", "unknown"), status="imported")
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.imported",
        "brc_package",
        result.get("manifest", {}).get("run_id", "import"),
        metadata={"battle_type": result.get("battle_type")},
    )
    return result
