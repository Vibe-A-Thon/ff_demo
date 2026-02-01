"""
Custom exception definitions for Fraud Forge.
"""

from __future__ import annotations

from typing import Optional


class AppError(Exception):
    """Base domain exception.

    Args:
        message: Human readable message.
        code: Stable error code.
        status_code: HTTP status code to return.
        detail: Optional detail for debugging.
    """

    def __init__(self, message: str, code: str, status_code: int, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail


class RuleValidationError(AppError):
    """Raised when rule validation fails."""

    def __init__(self, message: str = "Rule validation failed", detail: Optional[str] = None) -> None:
        super().__init__(message, code="rule_validation_error", status_code=400, detail=detail)


class RSBParseError(AppError):
    """Raised when RSB parsing fails."""

    def __init__(self, message: str = "RSB parse failed", detail: Optional[str] = None) -> None:
        super().__init__(message, code="rsb_parse_error", status_code=400, detail=detail)


class AgentExecutionError(AppError):
    """Raised when an agent execution fails."""

    def __init__(self, message: str = "Agent execution failed", detail: Optional[str] = None) -> None:
        super().__init__(message, code="agent_execution_error", status_code=500, detail=detail)
