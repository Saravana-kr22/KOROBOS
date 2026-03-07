"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Notes Service API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────────────────


class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    title: str = Field(..., min_length=1, max_length=500)
    content_md: str = Field(default="", description="Markdown content")
    tags: list[str] = Field(default_factory=list, description="Tag names")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content_md: Optional[str] = None
    tags: Optional[list[str]] = None


class NoteLinkCreate(BaseModel):
    """Schema for linking two notes."""

    target_note_id: UUID


# ── Response Schemas ──────────────────────────────────────────────────────


class NoteResponse(BaseModel):
    """Schema for a note in API responses."""

    id: UUID
    user_id: UUID
    title: str
    content_md: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Schema for paginated note list responses."""

    notes: list[NoteResponse]
    total: int


class NoteLinkResponse(BaseModel):
    """Schema for a note link in API responses."""

    id: UUID
    source_note_id: UUID
    target_note_id: UUID

    model_config = {"from_attributes": True}
