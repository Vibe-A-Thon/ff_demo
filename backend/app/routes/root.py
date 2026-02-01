"""Root and health routes."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import APP_NAME, APP_VERSION
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/")
async def root():
    """Return basic application metadata.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        dict: Application name and version.

    Raises:
        None: No explicit exceptions are raised.
    """
    logger.info("root.requested", extra={"payload": {"app": APP_NAME, "version": APP_VERSION}})
    return {"message": APP_NAME, "version": APP_VERSION}

@router.get("/health")
async def health():
    """Return service health status.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        dict: Health status and timestamp.

    Raises:
        None: No explicit exceptions are raised.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("health.checked", extra={"payload": {"status": "healthy", "timestamp": timestamp}})
    return {"status": "healthy", "timestamp": timestamp}
