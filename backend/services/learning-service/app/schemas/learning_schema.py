"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Learning Service.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Topic schemas
# ---------------------------------------------------------------------------


class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)


class TopicUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)


class TopicResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    topics: list[TopicResponse]
    total: int


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------


class LearningSessionCreate(BaseModel):
    """Manual session log — user provides topic and duration explicitly.

    Accepts either ``duration`` or the legacy ``duration_minutes`` field
    (Sprint_9.md Section 11 uses ``duration_minutes``).
    """

    topic: str = Field(..., min_length=1, max_length=300)
    duration: int = Field(..., gt=0, description="Duration in minutes")
    topic_id: Optional[UUID] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def accept_duration_minutes(cls, values: dict) -> dict:
        """Accept ``duration_minutes`` as an alias for ``duration``."""
        if isinstance(values, dict):
            if "duration_minutes" in values and "duration" not in values:
                values["duration"] = values.pop("duration_minutes")
        return values


class LearningSessionUpdate(BaseModel):
    topic: Optional[str] = Field(None, min_length=1, max_length=300)
    duration: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None


class LearningSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic: str
    topic_id: Optional[UUID]
    duration: int
    notes: Optional[str]
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearningSessionListResponse(BaseModel):
    sessions: list[LearningSessionResponse]
    total: int


# ---------------------------------------------------------------------------
# Timer schemas
# ---------------------------------------------------------------------------


class SessionStartRequest(BaseModel):
    """Start a live timer session."""

    topic: str = Field(..., min_length=1, max_length=300)
    topic_id: Optional[UUID] = None
    notes: Optional[str] = None


class SessionStopRequest(BaseModel):
    """Stop (complete) an active or paused session."""

    session_id: UUID
    notes: Optional[str] = None


class SessionPauseRequest(BaseModel):
    session_id: UUID


class SessionResumeRequest(BaseModel):
    session_id: UUID


# ---------------------------------------------------------------------------
# Note linking schemas
# ---------------------------------------------------------------------------


class LinkNoteRequest(BaseModel):
    note_id: UUID


class SessionNotesResponse(BaseModel):
    session_id: UUID
    note_ids: list[UUID]


# ---------------------------------------------------------------------------
# Analytics schemas
# ---------------------------------------------------------------------------


class LearningStatsResponse(BaseModel):
    total_sessions: int
    total_minutes: int
    topics: list[str]
    sessions_today: int
    current_streak: int
    weekly_minutes: int
    topic_distribution: dict[str, int]
