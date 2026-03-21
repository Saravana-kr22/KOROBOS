"""
KOROBOS — Database Service Pydantic Schemas

Request and response models for database, property, and record operations.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Request Models
# ============================================================================


class DatabaseCreate(BaseModel):
    """Create database request."""

    name: str = Field(..., min_length=1, max_length=500)
    icon: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class DatabaseUpdate(BaseModel):
    """Update database request."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    icon: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class PropertyCreate(BaseModel):
    """Create property request."""

    name: str = Field(..., min_length=1, max_length=200)
    type: Literal[
        "text",
        "number",
        "boolean",
        "date",
        "select",
        "multi_select",
        "relation",
    ]
    options: Optional[dict[str, Any]] = None
    position: int = Field(default=0, ge=0)


class RecordCreate(BaseModel):
    """Create record request."""

    values: dict[str, str] = Field(default_factory=dict)
    note_id: Optional[str] = None


class RecordUpdate(BaseModel):
    """Update record request."""

    values: dict[str, str] = Field(default_factory=dict)
    note_id: Optional[str] = None


class RecordFilter(BaseModel):
    """Record filter specification.

    Multiple filters are combined with AND logic.
    """

    property_id: Optional[UUID] = None
    operator: Literal["eq", "contains", "gt", "lt", "gte", "lte"] = "eq"
    value: Optional[str] = None


class RecordSort(BaseModel):
    """Record sort specification."""

    property_id: Optional[UUID] = None
    direction: Literal["asc", "desc"] = "asc"


# ============================================================================
# Response Models
# ============================================================================


class PropertyResponse(BaseModel):
    """Property response model."""

    id: UUID
    database_id: UUID
    name: str
    type: str
    options: Optional[dict[str, Any]]
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordValueResponse(BaseModel):
    """Record value response (property + value pair)."""

    property_id: UUID
    value: Optional[str]

    model_config = {"from_attributes": True}


class RecordResponse(BaseModel):
    """Record response model."""

    id: UUID
    database_id: UUID
    note_id: Optional[UUID]
    values: list[RecordValueResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatabaseResponse(BaseModel):
    """Database response model with properties and metadata."""

    id: UUID
    user_id: UUID
    name: str
    icon: Optional[str]
    description: Optional[str]
    properties: list[PropertyResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# List Response Models
# ============================================================================


class DatabaseListResponse(BaseModel):
    """Paginated database list response."""

    databases: list[DatabaseResponse]
    total: int
    page: int
    limit: int
    pages: int


class RecordListResponse(BaseModel):
    """Paginated record list response."""

    records: list[RecordResponse]
    total: int
    page: int
    limit: int
    pages: int


class DatabaseStatsResponse(BaseModel):
    """Database statistics response."""

    total_databases: int
    records_created_today: int
