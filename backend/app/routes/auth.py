"""Authentication routes.

Handles user registration and login.
"""

from typing import Dict
from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import UserCreate, UserLogin, User
from app.security import pwd_context, create_token
from app.core.rbac import PERMISSIONS
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/auth/register")
async def register(user_data: UserCreate) -> Dict[str, Dict[str, str]]:
    """Register a new user and issue a token.

    Args:
        user_data: User registration payload.

    Returns:
        Dict[str, Dict[str, str]]: Token and user summary.

    Raises:
        HTTPException: If role is unsupported or email exists.
    """
    if user_data.role not in PERMISSIONS:
        raise HTTPException(status_code=400, detail="Unsupported role")
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user_data.password)
    user = User(email=user_data.email, name=user_data.name, role=user_data.role)
    user_dict = user.model_dump()
    user_dict["password_hash"] = hashed_password

    await db.users.insert_one(user_dict)
    token = create_token(user.id, user.role)
    logger.info(
        "auth.registered",
        extra={"payload": {"user_id": user.id, "role": user.role}},
    )
    return {"token": token, "user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}}

@router.post("/auth/login")
async def login(login_data: UserLogin) -> Dict[str, Dict[str, str]]:
    """Authenticate a user and issue a token.

    Args:
        login_data: Login payload.

    Returns:
        Dict[str, Dict[str, str]]: Token and user summary.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = await db.users.find_one({"email": login_data.email}, {"_id": 0})
    if not user or not pwd_context.verify(login_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["id"], user["role"])
    logger.info(
        "auth.logged_in",
        extra={"payload": {"user_id": user["id"], "role": user["role"]}},
    )
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}}
