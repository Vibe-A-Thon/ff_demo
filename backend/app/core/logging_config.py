"""
Structured JSON logging configuration for Fraud Forge.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable
from app.core.request_context import get_correlation_id, get_request_id

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "authorization",
    "secret",
    "api_key",
    "jwt",
    "ssn",
    "account_number",
    "routing_number",
}


def redact_payload(payload: Any) -> Any:
    """Redact sensitive fields in structured payloads.

    Args:
        payload: Any structured object.

    Returns:
        Redacted payload.

    Raises:
        None: No explicit exceptions are raised.
    """
    if isinstance(payload, dict):
        redacted: Dict[str, Any] = {}
        for key, value in payload.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_payload(value)
        return redacted
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    return payload


class RedactingJsonFormatter(logging.Formatter):
    """JSON formatter that injects request context and redacts payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into JSON.

        Args:
            record: Log record instance.

        Returns:
            str: JSON-formatted log record.

        Raises:
            None: No explicit exceptions are raised.
        """
        message = record.getMessage()
        payload = getattr(record, "payload", None)
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "service_name": getattr(record, "service_name", None),
            "correlation_id": get_correlation_id(),
            "request_id": get_request_id(),
        }
        if payload is not None:
            log_record["payload"] = redact_payload(payload)
        return json.dumps(log_record, default=str)


def setup_logging(service_name: str = "fraud-forge") -> None:
    """Configure root logging to emit structured JSON.

    Args:
        service_name: Service name for log records.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """
    handler = logging.StreamHandler()
    formatter = RedactingJsonFormatter()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    root = logging.LoggerAdapter(root, {"service_name": service_name})


def get_logger(name: str, service_name: str = "fraud-forge") -> logging.LoggerAdapter:
    """Create a logger adapter with service metadata.

    Args:
        name: Logger name.
        service_name: Service identifier.

    Returns:
        Logger adapter instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = RedactingJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logging.LoggerAdapter(logger, {"service_name": service_name})


def coerce_log_payload(extra: Dict[str, Any], allowed_keys: Iterable[str] = ("payload",)) -> Dict[str, Any]:
    """Filter log extras to known keys.

    Args:
        extra: Extra fields for logging.
        allowed_keys: Keys permitted in log extras.

    Returns:
        Filtered dictionary.

    Raises:
        None: No explicit exceptions are raised.
    """
    return {key: value for key, value in extra.items() if key in allowed_keys}
