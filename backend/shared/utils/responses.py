"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Response Schemas ──────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    """Structured error detail within an API response."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class APIResponse(BaseModel):
    """Standard envelope for all CortexOS API responses."""

    status: str = Field(..., description="'success' or 'error'")
    data: Optional[Any] = Field(default=None, description="Response payload")
    error: Optional[ErrorDetail] = Field(default=None, description="Error details")


# ── Helper Functions ──────────────────────────────────────────────────────


def success_response(data: Any = None) -> dict[str, Any]:
    """
    Build a standardized success response.

    Example:
        {"status": "success", "data": {"id": "..."}}
    """
    return {"status": "success", "data": data}


def error_response(code: str, message: str) -> dict[str, Any]:
    """
    Build a standardized error response.

    Example:
        {"status": "error", "error": {"code": "RESOURCE_NOT_FOUND", "message": "..."}}
    """
    return {"status": "error", "error": {"code": code, "message": message}}
