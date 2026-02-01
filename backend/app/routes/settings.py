"""Platform settings routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import get_integration_setting
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.deps import get_db
from app.security import require_permission
from app.core.external_services import DatabaseClient

router = APIRouter()
logger = get_logger(__name__)


class RAGSettings(BaseModel):
    faithfulness_drop: float = 0.05
    relevancy_drop: float = 0.05
    faithfulness_warn: float = 0.75
    relevancy_warn: float = 0.75
    hit_rate_warn: float = 0.6
    hit_rate_crit: float = 0.4
    cache_dir: str = ""
    cache_ttl_seconds: int = 600
    cache_max_items: int = 200


class LLMSettings(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    version_pin: str = ""
    api_key: str = ""
    base_url: str = ""


class PlatformSettings(BaseModel):
    rag: RAGSettings
    llm: LLMSettings


def _default_settings() -> PlatformSettings:
    return PlatformSettings(
        rag=RAGSettings(
            faithfulness_drop=float(get_integration_setting("rag_evaluation", "faithfulness_drop", "0.05") or 0.05),
            relevancy_drop=float(get_integration_setting("rag_evaluation", "relevancy_drop", "0.05") or 0.05),
            faithfulness_warn=0.75,
            relevancy_warn=0.75,
            hit_rate_warn=0.6,
            hit_rate_crit=0.4,
            cache_dir=str(get_integration_setting("model_cache", "shared_dir", "") or ""),
            cache_ttl_seconds=600,
            cache_max_items=200,
        ),
        llm=LLMSettings(
            provider=str(get_integration_setting("llm", "provider", "openai") or "openai"),
            model=str(get_integration_setting("llm", "model", "gpt-4o-mini") or "gpt-4o-mini"),
            version_pin=str(get_integration_setting("llm", "version_pin", "") or ""),
            api_key="",
            base_url=str(get_integration_setting("llm", "base_url", "") or ""),
        ),
    )


@router.get("/settings")
async def get_settings(
    current_user: dict = Depends(require_permission("settings:read")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Get platform settings."""
    record = await db.platform_settings.find_one({"key": "global"}, {"_id": 0})
    if record and "payload" in record:
        payload = record.get("payload")
    else:
        payload = _default_settings().model_dump()
    await record_audit(
        current_user.get("id", "unknown"),
        "settings.read",
        "platform_settings",
        "global",
    )
    return payload


@router.put("/settings")
async def update_settings(
    settings: PlatformSettings,
    current_user: dict = Depends(require_permission("settings:write")),
    db: DatabaseClient = Depends(get_db),
) -> Dict[str, Any]:
    """Update platform settings."""
    payload = settings.model_dump()
    await db.platform_settings.update_one(
        {"key": "global"},
        {"$set": {"key": "global", "payload": payload}},
        upsert=True,
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "settings.update",
        "platform_settings",
        "global",
        metadata=payload,
    )
    logger.info("settings.update", extra={"payload": payload})
    return payload
