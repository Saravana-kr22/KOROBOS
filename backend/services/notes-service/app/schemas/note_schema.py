"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Notes Service API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content_md: str = Field(default="", description="Markdown content")
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content_md: Optional[str] = None
    tags: Optional[list[str]] = None


class NoteLinkCreate(BaseModel):
    target_note_id: UUID


class NoteResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content_md: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
    total: int
    page: int
    limit: int
    pages: int


class BacklinkListResponse(BaseModel):
    backlinks: list[NoteResponse]
    total: int


class NoteLinkResponse(BaseModel):
    id: UUID
    source_note_id: UUID
    target_note_id: UUID

    model_config = {"from_attributes": True}
