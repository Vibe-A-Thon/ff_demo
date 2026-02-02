"""Brain Surgery API routes for hot-swap, merge, and rollback operations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import Optional

from app.audit import record_audit
from app.core.logging_config import get_logger
from app.security import require_permission
from app.services.capsules.amc.brain_surgery_service import brain_surgery_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/brain-surgery/sessions")
async def start_surgery_session(
    team_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_permission("amc:write")),
):
    """
    Start a new brain surgery session for a team.
    Optionally upload an AMC file to analyze immediately.
    """
    try:
        amc_payload = None
        if file:
            amc_payload = await file.read()
        
        session = await brain_surgery_service.start_surgery_session(
            team_id=team_id,
            actor_id=current_user.get("id", "unknown"),
            amc_payload=amc_payload,
        )
        
        await record_audit(
            current_user.get("id", "unknown"),
            "brain_surgery.session_started",
            "brain_surgery_session",
            session.get("session_id"),
            metadata={"team_id": team_id},
        )
        
        return session
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/brain-surgery/sessions")
async def list_sessions(
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """List brain surgery sessions with optional filters."""
    return await brain_surgery_service.list_sessions(
        team_id=team_id,
        status=status,
        limit=limit,
    )


@router.get("/brain-surgery/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """Get a specific brain surgery session."""
    session = await brain_surgery_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/brain-surgery/sessions/{session_id}/analyze")
async def analyze_amc_for_session(
    session_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("amc:write")),
):
    """Upload and analyze an AMC file for an existing session."""
    session = await brain_surgery_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    amc_payload = await file.read()
    
    # Re-analyze with the new payload
    updated_session = await brain_surgery_service.start_surgery_session(
        team_id=session.get("team_id"),
        actor_id=current_user.get("id", "unknown"),
        amc_payload=amc_payload,
    )
    
    await record_audit(
        current_user.get("id", "unknown"),
        "brain_surgery.amc_analyzed",
        "brain_surgery_session",
        session_id,
    )
    
    return updated_session


@router.post("/brain-surgery/sessions/{session_id}/resolve-conflict")
async def resolve_conflict(
    session_id: str,
    conflict_id: str = Form(...),
    resolution: str = Form(...),
    current_user: dict = Depends(require_permission("amc:write")),
):
    """Resolve a conflict in a brain surgery session."""
    try:
        session = await brain_surgery_service.resolve_conflict(
            session_id=session_id,
            conflict_id=conflict_id,
            resolution=resolution,
            actor_id=current_user.get("id", "unknown"),
        )
        
        await record_audit(
            current_user.get("id", "unknown"),
            "brain_surgery.conflict_resolved",
            "brain_surgery_session",
            session_id,
            metadata={"conflict_id": conflict_id, "resolution": resolution},
        )
        
        return session
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/brain-surgery/sessions/{session_id}/sandbox")
async def run_sandbox_validation(
    session_id: str,
    current_user: dict = Depends(require_permission("amc:write")),
):
    """Run sandbox validation tests on the merged APMC state."""
    try:
        session = await brain_surgery_service.run_sandbox_validation(
            session_id=session_id,
            actor_id=current_user.get("id", "unknown"),
        )
        
        await record_audit(
            current_user.get("id", "unknown"),
            "brain_surgery.sandbox_executed",
            "brain_surgery_session",
            session_id,
            metadata={"passed": session.get("sandbox_results", {}).get("passed")},
        )
        
        return session
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/brain-surgery/sessions/{session_id}/hot-swap")
async def execute_hot_swap(
    session_id: str,
    mode: str = Form("hot_swap"),
    current_user: dict = Depends(require_permission("amc:approve")),
):
    """
    Execute the hot-swap operation to activate merged APMC state.
    Requires amc:approve permission (SoD enforced).
    
    Modes:
    - hot_swap: Immediate activation with auto-rollback capability
    - gradual: Phased rollout with checkpoints
    - shadow: Shadow mode - run in parallel for comparison
    """
    try:
        session = await brain_surgery_service.execute_hot_swap(
            session_id=session_id,
            actor_id=current_user.get("id", "unknown"),
            mode=mode,
        )
        
        await record_audit(
            current_user.get("id", "unknown"),
            "brain_surgery.hot_swap_executed",
            "brain_surgery_session",
            session_id,
            metadata={"mode": mode, "team_id": session.get("team_id")},
        )
        
        return session
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/brain-surgery/rollback")
async def execute_rollback(
    team_id: str = Form(...),
    snapshot_id: Optional[str] = Form(None),
    current_user: dict = Depends(require_permission("amc:approve")),
):
    """
    Rollback to a previous APMC state.
    If snapshot_id is not provided, rolls back to the most recent snapshot.
    """
    try:
        result = await brain_surgery_service.execute_rollback(
            team_id=team_id,
            snapshot_id=snapshot_id,
            actor_id=current_user.get("id", "unknown"),
        )
        
        await record_audit(
            current_user.get("id", "unknown"),
            "brain_surgery.rollback_executed",
            "amc_rollback",
            result.get("rollback", {}).get("rollback_id"),
            metadata={"team_id": team_id, "snapshot_id": snapshot_id},
        )
        
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/brain-surgery/teams/{team_id}/state")
async def get_active_state(
    team_id: str,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """Get the currently active APMC state for a team."""
    return await brain_surgery_service.get_active_state(team_id)


@router.get("/brain-surgery/teams/{team_id}/rollback-snapshots")
async def list_rollback_snapshots(
    team_id: str,
    limit: int = 10,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """List available rollback snapshots for a team."""
    return await brain_surgery_service.list_rollback_snapshots(team_id, limit)


@router.get("/brain-surgery/sessions/{session_id}/knowledge-graph")
async def get_knowledge_graph(
    session_id: str,
    current_user: dict = Depends(require_permission("amc:read")),
):
    """
    Get the knowledge graph representation for Brain Surgery merge visualization.
    Returns nodes and edges for baseline, import, and merged states.
    """
    try:
        return await brain_surgery_service.get_knowledge_graph_for_merge(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
