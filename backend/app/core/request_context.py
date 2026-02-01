"""
Request context utilities for correlation and request IDs.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_correlation_id(value: Optional[str]) -> None:
    """Set the correlation ID for the current context.

    Args:
        value: Correlation ID value to set.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """
    correlation_id_var.set(value)


def set_request_id(value: Optional[str]) -> None:
    """Set the request ID for the current context.

    Args:
        value: Request ID value to set.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """
    request_id_var.set(value)


def get_correlation_id() -> Optional[str]:
    """Return the current correlation ID.

    Returns:
        Current correlation ID if set; otherwise None.

    Raises:
        None: No explicit exceptions are raised.
    """
    return correlation_id_var.get()


def get_request_id() -> Optional[str]:
    """Return the current request ID.

    Returns:
        Current request ID if set; otherwise None.

    Raises:
        None: No explicit exceptions are raised.
    """
    return request_id_var.get()
