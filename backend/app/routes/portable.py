"""
Portable Intelligence API Routes

Provides endpoints for exporting and importing AI brain packages:
- POST /api/portable/export/pep - Export Portable Evolution Pack
- POST /api/portable/export/rsb - Export Rule Suite Box
- POST /api/portable/export/brc - Export Brain Capsule
- POST /api/portable/import - Import any package type
- POST /api/portable/validate - Validate package without importing
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.external_services import DatabaseClient, LLMClient
from app.dependencies import get_db, get_llm_client
from app.security import require_permission
from app.core.logging_config import get_logger
from app.services.portable_intelligence import (
    PortableIntelligenceService,
    PackageType,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/portable", tags=["portable"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportPEPRequest(BaseModel):
    """Request to export a PEP package."""
    name: str = Field(..., description="Package name")
    description: str = Field(default="", description="Package description")
    collections: Optional[List[str]] = Field(
        default=None,
        description="RAG collections to include (attacks, patterns, taxonomy, rules, explanations)"
    )
    anonymize: bool = Field(default=True, description="Whether to anonymize sensitive data")
    include_evolution: bool = Field(default=True, description="Include evolution history")
    agent_ids: Optional[List[str]] = Field(default=None, description="Specific agents to include")


class ExportRSBRequest(BaseModel):
    """Request to export an RSB package."""
    name: str = Field(..., description="Package name")
    rule_ids: Optional[List[str]] = Field(default=None, description="Specific rule IDs (None = all)")
    include_tests: bool = Field(default=True, description="Include test cases")


class ExportBRCRequest(BaseModel):
    """Request to export a full Brain Capsule."""
    name: str = Field(..., description="Package name")
    description: str = Field(default="", description="Package description")


class ImportRequest(BaseModel):
    """Request to import a package."""
    merge_mode: str = Field(
        default="merge",
        description="How to handle conflicts: merge, replace, skip_existing"
    )
    validate_checksum: bool = Field(default=True, description="Validate package integrity")


class PackageInfo(BaseModel):
    """Information about a package."""
    package_id: str
    package_type: str
    name: str
    description: Optional[str]
    version: str
    created_at: str
    contents: Dict[str, Any]


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/export/pep")
async def export_pep(
    request: ExportPEPRequest,
    current_user: dict = Depends(require_permission("portable:export")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> StreamingResponse:
    """
    Export a Portable Evolution Pack (PEP).
    
    A PEP contains:
    - Selected RAG memories (anonymized if requested)
    - Evolution/learning history
    - Agent profiles
    
    Returns a downloadable .pep (zip) file.
    """
    service = PortableIntelligenceService(db, llm_client)
    
    try:
        zip_buffer = await service.export_pep(
            name=request.name,
            description=request.description,
            collections=request.collections,
            anonymize=request.anonymize,
            include_evolution=request.include_evolution,
            agent_ids=request.agent_ids,
        )
        
        filename = f"{request.name.replace(' ', '_').lower()}.pep"
        
        logger.info(
            "api.portable.export.pep",
            extra={"payload": {"name": request.name}}
        )
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(
            "api.portable.export.pep.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/rsb")
async def export_rsb(
    request: ExportRSBRequest,
    current_user: dict = Depends(require_permission("portable:export")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> StreamingResponse:
    """
    Export a Rule Suite Box (RSB).
    
    An RSB contains:
    - Rule definitions
    - Test cases (optional)
    
    Returns a downloadable .rsb (zip) file.
    """
    service = PortableIntelligenceService(db, llm_client)
    
    try:
        zip_buffer = await service.export_rsb(
            name=request.name,
            rule_ids=request.rule_ids,
            include_tests=request.include_tests,
        )
        
        filename = f"{request.name.replace(' ', '_').lower()}.rsb"
        
        logger.info(
            "api.portable.export.rsb",
            extra={"payload": {"name": request.name}}
        )
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(
            "api.portable.export.rsb.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/brc")
async def export_brc(
    request: ExportBRCRequest,
    current_user: dict = Depends(require_permission("portable:export")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> StreamingResponse:
    """
    Export a Brain Capsule (BRC) - complete brain state.
    
    A BRC contains:
    - All RAG collections
    - Knowledge graph nodes
    - All agents
    - All rules
    - Learning events
    
    Returns a downloadable .brc (zip) file.
    """
    service = PortableIntelligenceService(db, llm_client)
    
    try:
        zip_buffer = await service.export_brc(
            name=request.name,
            description=request.description,
        )
        
        filename = f"{request.name.replace(' ', '_').lower()}.brc"
        
        logger.info(
            "api.portable.export.brc",
            extra={"payload": {"name": request.name}}
        )
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(
            "api.portable.export.brc.failed",
            extra={"payload": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Import Endpoints
# ============================================================================

@router.post("/import")
async def import_package(
    file: UploadFile = File(...),
    merge_mode: str = Query("merge", description="merge, replace, or skip_existing"),
    validate_checksum: bool = Query(True, description="Validate package integrity"),
    current_user: dict = Depends(require_permission("portable:import")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Import a portable intelligence package.
    
    Accepts .pep, .apmc, .rsb, or .brc files.
    Automatically detects package type from manifest.
    
    Args:
        file: The package file to import
        merge_mode: How to handle conflicts (merge, replace, skip_existing)
        validate_checksum: Whether to validate package integrity
        
    Returns:
        Import results including counts of imported items
    """
    service = PortableIntelligenceService(db, llm_client)
    
    try:
        # Read file content
        content = await file.read()
        
        # Import the package
        result = await service.import_package(
            file_content=content,
            merge_mode=merge_mode,
            validate_checksum=validate_checksum,
        )
        
        logger.info(
            "api.portable.import.complete",
            extra={"payload": {"filename": file.filename, "result": result}}
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "api.portable.import.failed",
            extra={"payload": {"filename": file.filename, "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_package(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_permission("portable:read")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    Validate a package without importing it.
    
    Returns package manifest and validation status.
    Useful for previewing what will be imported.
    """
    service = PortableIntelligenceService(db, llm_client)
    
    try:
        content = await file.read()
        result = await service.validate_package(content)
        
        return {
            "filename": file.filename,
            **result,
        }
        
    except Exception as e:
        logger.error(
            "api.portable.validate.failed",
            extra={"payload": {"filename": file.filename, "error": str(e)}}
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_export_import_history(
    limit: int = Query(50, description="Maximum items to return"),
    current_user: dict = Depends(require_permission("portable:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get history of exports and imports.
    """
    exports = await db.export_logs.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    imports = await db.import_logs.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "exports": exports,
        "imports": imports,
    }
