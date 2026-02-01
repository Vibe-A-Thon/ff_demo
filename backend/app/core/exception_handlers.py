"""
Global exception handling registration.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from app.core.exceptions import AppError
from app.core.logging_config import get_logger
from app.core.request_context import get_correlation_id

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers.

    Args:
        app: FastAPI application instance.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        correlation_id = get_correlation_id()
        logger.exception(
            "Domain error",
            extra={"payload": {"error": exc.code, "detail": exc.detail, "correlation_id": correlation_id}},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "detail": exc.detail,
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        correlation_id = get_correlation_id()
        logger.warning(
            "HTTP error",
            extra={"payload": {"status_code": exc.status_code, "detail": exc.detail, "correlation_id": correlation_id}},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": exc.detail,
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        correlation_id = get_correlation_id()
        logger.exception(
            "Unhandled exception",
            extra={"payload": {"correlation_id": correlation_id}},
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id,
            },
        )
