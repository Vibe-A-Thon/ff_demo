from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import APP_NAME, APP_VERSION
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def root():
    logger.info("root.requested", extra={"payload": {"app": APP_NAME, "version": APP_VERSION}})
    return {"message": APP_NAME, "version": APP_VERSION}

@router.get("/health")
async def health():
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("health.checked", extra={"payload": {"status": "healthy", "timestamp": timestamp}})
    return {"status": "healthy", "timestamp": timestamp}
