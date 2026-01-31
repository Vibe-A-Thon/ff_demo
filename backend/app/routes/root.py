from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import APP_NAME, APP_VERSION

router = APIRouter()

@router.get("/")
async def root():
    return {"message": APP_NAME, "version": APP_VERSION}

@router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
