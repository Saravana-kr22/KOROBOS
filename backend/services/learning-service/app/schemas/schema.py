"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LearningSessionCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    duration: int = Field(..., gt=0, description="Duration in minutes")
    notes: Optional[str] = None


class LearningSessionUpdate(BaseModel):
    topic: Optional[str] = Field(None, min_length=1, max_length=300)
    duration: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None


class LearningSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic: str
    duration: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearningSessionListResponse(BaseModel):
    sessions: list[LearningSessionResponse]
    total: int


class LearningStatsResponse(BaseModel):
    total_sessions: int
    total_minutes: int
    topics: list[str]
