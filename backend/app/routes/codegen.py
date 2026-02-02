"""RuleSpec to Code Pipeline routes.

API endpoints for converting RuleSpec artifacts to production Python code.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.core.external_services import DatabaseClient
from app.core.logging_config import get_logger
from app.deps import get_db
from app.security import require_permission
from app.audit import record_audit
from app.services.codegen.rule_code_generator import rule_code_generator
from app.services.codegen.code_deployment_service import code_deployment_service


router = APIRouter()
logger = get_logger(__name__)


class CodeGenerationRequest(BaseModel):
    """Request to generate code from RuleSpec."""
    artifact_id: str
    deployment_mode: str = "sandbox"  # sandbox, staging, production


class CodeDeploymentRequest(BaseModel):
    """Request to deploy generated code."""
    rule_id: str
    mode: str = "sandbox"


class PromotionRequest(BaseModel):
    """Request to promote rule deployment."""
    from_mode: str
    to_mode: str


@router.post("/codegen/generate")
async def generate_code_from_rulespec(
    request: CodeGenerationRequest,
    current_user: dict = Depends(require_permission("rules:write")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Generate Python code from a RuleSpec artifact.

    Args:
        request: Code generation request.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Generated code and metadata.

    Raises:
        HTTPException: If artifact not found or generation fails.
    """
    # Fetch the RuleSpec artifact
    artifact = await db.artifacts.find_one(
        {"artifact_id": request.artifact_id, "artifact_type": "RuleSpec"},
        {"_id": 0}
    )
    
    if not artifact:
        raise HTTPException(status_code=404, detail="RuleSpec artifact not found")
    
    # Extract RuleSpec from artifact
    rulespec = artifact.get("data", {})
    
    if not rulespec:
        raise HTTPException(status_code=400, detail="Invalid RuleSpec artifact")
    
    # Generate code
    try:
        result = rule_code_generator.generate_code(rulespec)
    except Exception as e:
        logger.error("code_generation_failed", extra={"error": str(e), "artifact_id": request.artifact_id})
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")
    
    # Validate generated code
    validation = rule_code_generator.validate_generated_code(result["code"])
    result["validation"] = validation
    
    if not validation["valid"]:
        logger.warning(
            "code_generation_validation_failed",
            extra={"artifact_id": request.artifact_id, "errors": validation["errors"]}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Generated code validation failed: {validation['errors']}"
        )
    
    # Store generated code as CodePatch artifact
    code_patch_artifact = {
        "artifact_id": f"codepatch_{result['rule_id']}_{result['hash'][:8]}",
        "artifact_type": "CodePatch",
        "source_artifact_id": request.artifact_id,
        "rule_id": result["rule_id"],
        "code": result["code"],
        "hash": result["hash"],
        "language": result["language"],
        "framework": result["framework"],
        "generated_at": result["generated_at"],
        "generated_by": current_user.get("id", "unknown"),
        "validation": validation,
        "status": "generated",
        "metadata": result["metadata"],
    }
    
    await db.artifacts.insert_one(code_patch_artifact)
    
    # Audit log
    await record_audit(
        current_user.get("id", "unknown"),
        "code.generated",
        "codepatch",
        code_patch_artifact["artifact_id"],
        metadata={
            "rule_id": result["rule_id"],
            "source_artifact": request.artifact_id,
        },
    )
    
    logger.info(
        "code.generated",
        extra={
            "payload": {
                "artifact_id": code_patch_artifact["artifact_id"],
                "rule_id": result["rule_id"],
            }
        },
    )
    
    return {
        "artifact_id": code_patch_artifact["artifact_id"],
        "rule_id": result["rule_id"],
        "code": result["code"],
        "hash": result["hash"],
        "validation": validation,
        "metadata": result["metadata"],
    }


@router.post("/codegen/deploy/{artifact_id}")
async def deploy_generated_code(
    artifact_id: str,
    request: CodeDeploymentRequest,
    current_user: dict = Depends(require_permission("rules:deploy")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Deploy generated code to an environment.

    Args:
        artifact_id: CodePatch artifact ID.
        request: Deployment request.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Deployment result.

    Raises:
        HTTPException: If artifact not found or deployment fails.
    """
    # Fetch CodePatch artifact
    artifact = await db.artifacts.find_one(
        {"artifact_id": artifact_id, "artifact_type": "CodePatch"},
        {"_id": 0}
    )
    
    if not artifact:
        raise HTTPException(status_code=404, detail="CodePatch artifact not found")
    
    # Check validation status
    if not artifact.get("validation", {}).get("valid"):
        raise HTTPException(status_code=400, detail="Cannot deploy invalid code")
    
    # Deploy code
    try:
        deployment_result = code_deployment_service.deploy_code(
            rule_id=artifact["rule_id"],
            code=artifact["code"],
            metadata=artifact.get("metadata", {}),
            mode=request.mode,
        )
    except Exception as e:
        logger.error("code_deployment_failed", extra={"error": str(e), "artifact_id": artifact_id})
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")
    
    # Update artifact status
    await db.artifacts.update_one(
        {"artifact_id": artifact_id},
        {"$set": {"status": "deployed", "deployment": deployment_result}}
    )
    
    # Audit log
    await record_audit(
        current_user.get("id", "unknown"),
        "code.deployed",
        "codepatch",
        artifact_id,
        metadata={
            "rule_id": artifact["rule_id"],
            "mode": request.mode,
            "file_path": deployment_result["file_path"],
        },
    )
    
    logger.info(
        "code.deployed",
        extra={
            "payload": {
                "artifact_id": artifact_id,
                "rule_id": artifact["rule_id"],
                "mode": request.mode,
            }
        },
    )
    
    return deployment_result


@router.get("/codegen/deployments")
async def list_deployments(
    mode: str = None,
    current_user: dict = Depends(require_permission("rules:read")),
) -> Dict[str, Any]:
    """List deployed rules.

    Args:
        mode: Optional deployment mode filter.
        current_user: Authorized user context.

    Returns:
        List of deployed rules.
    """
    deployments = code_deployment_service.list_deployed_rules(mode=mode)
    
    return {
        "deployments": deployments,
        "total": len(deployments),
    }


@router.post("/codegen/promote/{rule_id}")
async def promote_deployment(
    rule_id: str,
    request: PromotionRequest,
    current_user: dict = Depends(require_permission("rules:deploy")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Promote a rule deployment from one environment to another.

    Args:
        rule_id: Rule identifier.
        request: Promotion request.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Promotion result.

    Raises:
        HTTPException: If promotion fails.
    """
    try:
        result = code_deployment_service.promote_deployment(
            rule_id=rule_id,
            from_mode=request.from_mode,
            to_mode=request.to_mode,
        )
    except Exception as e:
        logger.error("deployment_promotion_failed", extra={"error": str(e), "rule_id": rule_id})
        raise HTTPException(status_code=500, detail=f"Promotion failed: {str(e)}")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Promotion failed"))
    
    # Audit log
    await record_audit(
        current_user.get("id", "unknown"),
        "code.promoted",
        "deployment",
        rule_id,
        metadata={
            "from_mode": request.from_mode,
            "to_mode": request.to_mode,
        },
    )
    
    logger.info(
        "code.promoted",
        extra={
            "payload": {
                "rule_id": rule_id,
                "from_mode": request.from_mode,
                "to_mode": request.to_mode,
            }
        },
    )
    
    return result


@router.post("/codegen/rollback/{rule_id}")
async def rollback_deployment(
    rule_id: str,
    current_user: dict = Depends(require_permission("rules:deploy")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Rollback a deployed rule.

    Args:
        rule_id: Rule identifier.
        current_user: Authorized user context.
        db: Database client.

    Returns:
        Rollback result.

    Raises:
        HTTPException: If rollback fails.
    """
    try:
        result = code_deployment_service.rollback_deployment(rule_id)
    except Exception as e:
        logger.error("deployment_rollback_failed", extra={"error": str(e), "rule_id": rule_id})
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Rollback failed"))
    
    # Audit log
    await record_audit(
        current_user.get("id", "unknown"),
        "code.rolled_back",
        "deployment",
        rule_id,
    )
    
    logger.info(
        "code.rolled_back",
        extra={"payload": {"rule_id": rule_id}},
    )
    
    return result


@router.get("/codegen/validate/{rule_id}")
async def validate_deployment(
    rule_id: str,
    current_user: dict = Depends(require_permission("rules:read")),
) -> Dict[str, Any]:
    """Validate a deployed rule.

    Args:
        rule_id: Rule identifier.
        current_user: Authorized user context.

    Returns:
        Validation result.
    """
    result = code_deployment_service.validate_deployment(rule_id)
    
    return result
