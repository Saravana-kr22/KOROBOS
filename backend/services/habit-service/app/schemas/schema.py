"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Habit Service API.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    frequency: str = Field(default="daily", description="daily, weekly, monthly")
    description: Optional[str] = None


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    frequency: Optional[str] = None
    description: Optional[str] = None


class HabitResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    frequency: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HabitCompleteRequest(BaseModel):
    log_date: date = Field(default_factory=date.today)


class HabitCompleteResponse(BaseModel):
    habit_id: UUID
    completed: bool
    streak: int


class HabitListResponse(BaseModel):
    habits: list[HabitResponse]
    total: int
