"""Authentication and RBAC helpers for API security."""

from typing import Any, Callable, Dict
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timezone
from app.config import JWT_SECRET, JWT_ALGORITHM
from app.db import db
from app.core.logging_config import get_logger
from app.core.rbac import has_permission

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
logger = get_logger(__name__)

def create_token(user_id: str, role: str) -> str:
    """Create a JWT token for a user.

    Args:
        user_id: User identifier.
        role: User role.

    Returns:
        str: Encoded JWT token.

    Raises:
        None: No explicit exceptions are raised.
    """
    payload = {"sub": user_id, "role": role, "exp": datetime.now(timezone.utc).timestamp() + 86400}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Resolve current user from JWT token.

    Args:
        credentials: Authorization credentials.

    Returns:
        Dict[str, Any]: User document.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError as exc:
        logger.warning("Invalid token", extra={"payload": {"reason": str(exc)}})
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def require_permission(permission: str) -> Callable[..., Any]:
    """Create a dependency that enforces permissions.

    Args:
        permission: Permission string.

    Returns:
        Callable[..., Any]: Dependency callable.

    Raises:
        None: No explicit exceptions are raised.
    """
    async def _require(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = current_user.get("role", "")
        if not has_permission(role, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return _require
