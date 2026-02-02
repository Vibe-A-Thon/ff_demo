"""BRC capsule routes - Complete API for Battle Run Capsules.

Provides endpoints for:
- BRC validation, preview, import
- BRC export from battles
- BRC catalog management
- Replay modes (read-only, re-evaluate, rerun-defense)
- BRC comparison
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
try:
    from fastapi.responses import Response, StreamingResponse
except ModuleNotFoundError:
    from starlette.responses import Response, StreamingResponse

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.db import db
from app.security import require_permission
from app.services.capsules.brc.brc_service import (
    validate_brc_bytes,
    preview_brc_bytes,
    import_brc_bytes,
    persist_brc_package,
    build_brc_archive,
)
from app.services.capsules.brc.replay_engine import (
    replay_engine,
    compare_brcs,
    ReplayMode,
)
from app.services.capsules.brc.postmortem_generator import (
    postmortem_generator,
    generate_and_save_postmortem,
)

router = APIRouter()
logger = get_logger(__name__)


# ============================================================================
# Core BRC Operations
# ============================================================================

@router.post("/brc/validate")
async def validate_brc(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Validate a BRC archive.
    
    Performs:
    - ZIP structure validation
    - Required files check
    - Schema validation
    - Hash verification
    - Prohibited content scan
    """
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
async def preview_brc(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Preview a BRC archive without importing."""
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
async def import_brc(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("battle:write")),
):
    """Import a BRC archive into the system."""
    payload = await file.read()
    try:
        result = import_brc_bytes(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    package = await persist_brc_package(
        payload,
        result.get("manifest", {}),
        current_user.get("id", "unknown"),
        status="imported",
    )
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.imported",
        "brc_package",
        result.get("manifest", {}).get("run_id", "import"),
        metadata={"battle_type": result.get("battle_type"), "package_id": package.get("id")},
    )
    
    return {**result, "package_id": package.get("id")}


@router.post("/brc/export")
async def export_brc(
    battle_id: str = Form(...),
    include_telemetry: bool = Form(True),
    include_graphs: bool = Form(True),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Export a battle run as BRC archive.
    
    Args:
        battle_id: The battle run ID to export
        include_telemetry: Include telemetry data
        include_graphs: Include graph visualizations
    """
    # Get battle run data
    run = await db.battle_runs.find_one({"id": battle_id}, {"_id": 0})
    if not run:
        # Try battles collection
        run = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    
    if not run:
        raise HTTPException(status_code=404, detail="Battle run not found")
    
    # Get events
    events = await db.battle_events.find(
        {"battle_run_id": battle_id},
        {"_id": 0},
    ).to_list(1000)
    
    # Build archive
    archive_bytes, manifest, archive_name = build_brc_archive(run, events)
    
    # Persist package
    package = await persist_brc_package(
        archive_bytes,
        manifest,
        current_user.get("id", "unknown"),
        status="exported",
    )
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.exported",
        "brc_package",
        battle_id,
        metadata={"package_id": package.get("id"), "archive_name": archive_name},
    )
    
    return StreamingResponse(
        iter([archive_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={archive_name}"},
    )


# ============================================================================
# BRC Catalog
# ============================================================================

@router.get("/brc/catalog")
async def list_brc_catalog(
    status: Optional[str] = Query(None, description="Filter by status (imported/exported)"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """List available BRC packages in the catalog."""
    query = {}
    if status:
        query["status"] = status
    
    packages = await db.brc_packages.find(
        query,
        {"_id": 0, "id": 1, "run_id": 1, "battle_type": 1, "status": 1, "created_at": 1, "created_by": 1},
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.catalog_listed",
        "brc_catalog",
        "list",
        metadata={"count": len(packages), "status_filter": status},
    )
    
    return {"packages": packages, "count": len(packages)}


@router.get("/brc/catalog/{package_id}")
async def get_brc_package(
    package_id: str,
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Get details of a specific BRC package."""
    package = await db.brc_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise HTTPException(status_code=404, detail="BRC package not found")
    
    return package


@router.delete("/brc/catalog/{package_id}")
async def delete_brc_package(
    package_id: str,
    current_user: dict = Depends(require_permission("battle:write")),
):
    """Delete a BRC package from the catalog."""
    result = await db.brc_packages.delete_one({"id": package_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="BRC package not found")
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.deleted",
        "brc_package",
        package_id,
    )
    
    return {"message": "BRC package deleted", "id": package_id}


# ============================================================================
# Replay Engine Routes
# ============================================================================

@router.post("/brc/replay/start")
async def start_replay_session(
    file: UploadFile = File(...),
    mode: str = Form("read_only"),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Start a new BRC replay session.
    
    Args:
        file: BRC archive to replay
        mode: Replay mode (read_only, reevaluate, rerun_defense)
    """
    payload = await file.read()
    
    # Validate first
    validation = validate_brc_bytes(payload)
    if not validation.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=f"BRC validation failed: {validation.get('errors', [])}",
        )
    
    try:
        replay_mode = ReplayMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid replay mode: {mode}. Valid: read_only, reevaluate, rerun_defense",
        )
    
    session = await replay_engine.start_replay_session(
        payload,
        replay_mode,
        current_user.get("id", "unknown"),
    )
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.replay_started",
        "brc_replay_session",
        session["session_id"],
        metadata={"mode": mode},
    )
    
    return session


@router.get("/brc/replay/sessions")
async def list_replay_sessions(
    mode: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """List replay sessions."""
    replay_mode = None
    if mode:
        try:
            replay_mode = ReplayMode(mode)
        except ValueError:
            pass
    
    sessions = await replay_engine.list_sessions(limit=limit, mode=replay_mode)
    return {"sessions": sessions, "count": len(sessions)}


@router.get("/brc/replay/sessions/{session_id}")
async def get_replay_session(
    session_id: str,
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Get a specific replay session."""
    session = await replay_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Replay session not found")
    return session


@router.post("/brc/replay/sessions/{session_id}/reevaluate")
async def reevaluate_session(
    session_id: str,
    current_user: dict = Depends(require_permission("battle:write")),
):
    """Re-evaluate a BRC with current scoring rules.
    
    This recomputes the scorecard without rerunning agents.
    """
    try:
        result = await replay_engine.reevaluate(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.reevaluated",
        "brc_replay_session",
        session_id,
        metadata={"improved": result.get("improved")},
    )
    
    return result


@router.post("/brc/replay/sessions/{session_id}/rerun-defense")
async def rerun_defense_session(
    session_id: str,
    improvement_factor: float = Form(0.1),
    current_user: dict = Depends(require_permission("battle:write")),
):
    """Rerun defense stages using stored Red inputs.
    
    This simulates what would happen with updated defense rules.
    
    Args:
        session_id: Replay session ID
        improvement_factor: Expected improvement factor (0.0-1.0)
    """
    try:
        result = await replay_engine.rerun_defense(
            session_id,
            defense_config={"improvement_factor": improvement_factor},
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.rerun_defense",
        "brc_replay_session",
        session_id,
        metadata={"improved": result.get("improved"), "improvement_factor": improvement_factor},
    )
    
    return result


# ============================================================================
# BRC Comparison
# ============================================================================

@router.post("/brc/compare")
async def compare_brc_files(
    before_file: UploadFile = File(...),
    after_file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Compare two BRC files and show score delta.
    
    Useful for comparing performance before/after tuning.
    """
    before_payload = await before_file.read()
    after_payload = await after_file.read()
    
    # Validate both
    for name, payload in [("before", before_payload), ("after", after_payload)]:
        validation = validate_brc_bytes(payload)
        if not validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail=f"BRC {name} validation failed: {validation.get('errors', [])}",
            )
    
    comparison = await compare_brcs(before_payload, after_payload)
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.compared",
        "brc_comparison",
        comparison["comparison_id"],
        metadata={"improved": comparison.get("improved")},
    )
    
    return comparison


# ============================================================================
# Postmortem Generation
# ============================================================================

@router.post("/brc/postmortem")
async def generate_postmortem(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Generate postmortem from BRC.
    
    Returns:
    - Postmortem markdown
    - Distilled lessons (for AMC)
    - RSB rule proposals
    """
    payload = await file.read()
    
    # Validate first
    validation = validate_brc_bytes(payload)
    if not validation.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=f"BRC validation failed: {validation.get('errors', [])}",
        )
    
    # Extract BRC data
    session = await replay_engine.start_replay_session(
        payload,
        ReplayMode.READ_ONLY,
        current_user.get("id", "unknown"),
    )
    
    # Generate postmortem
    battle_data = {
        "battle_type": session.get("manifest", {}).get("battle_type", "Unknown"),
        "run_id": session.get("manifest", {}).get("run_id", "N/A"),
    }
    scorecard = session.get("scorecard", {})
    stages = session.get("stages", {})
    
    postmortem = postmortem_generator.generate_postmortem(battle_data, scorecard, stages)
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brc.postmortem_generated",
        "brc_postmortem",
        session["session_id"],
    )
    
    return postmortem


@router.get("/brc/{battle_id}/postmortem")
async def get_battle_postmortem(
    battle_id: str,
    current_user: dict = Depends(require_permission("battle:read")),
):
    """Get or generate postmortem for a battle."""
    # Try to get existing
    postmortem = await db.battle_postmortems.find_one(
        {"battle_id": battle_id},
        {"_id": 0},
    )
    
    if postmortem:
        return postmortem
    
    # Generate new
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    # Use battle data to generate
    scorecard = battle.get("metrics", {})
    stages = {}  # Would be populated from battle events
    
    postmortem = await generate_and_save_postmortem(
        battle_id,
        scorecard,
        stages,
    )
    
    return postmortem
