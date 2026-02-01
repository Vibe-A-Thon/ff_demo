"""User identity routes."""

from typing import Dict
from fastapi import APIRouter, Depends
from app.security import get_current_user, require_permission
from app.audit import record_audit
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(require_permission("auth:read"))) -> Dict[str, str]:
    """Return the current authenticated user.

    Args:
        current_user: Authenticated user context.

    Returns:
        Dict[str, str]: User summary.

    Raises:
        None: No explicit exceptions are raised.
    """
    logger.info("auth.me", extra={"payload": {"user_id": current_user.get("id"), "role": current_user.get("role")}})
    await record_audit(
        current_user.get("id", "unknown"),
        "auth.me",
        "user",
        current_user.get("id", "unknown"),
    )
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "role": current_user["role"],
    }
