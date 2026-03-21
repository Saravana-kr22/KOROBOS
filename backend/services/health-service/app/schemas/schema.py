"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MealLogCreate(BaseModel):
    calories: int = Field(..., gt=0)
    food_name: Optional[str] = Field(None, max_length=500)
    protein: Optional[int] = Field(None, ge=0, description="Grams")
    carbs: Optional[int] = Field(None, ge=0, description="Grams")
    fat: Optional[int] = Field(None, ge=0, description="Grams")
    description: Optional[str] = None


class WorkoutLogCreate(BaseModel):
    duration: int = Field(..., gt=0, description="Minutes")
    calories: Optional[int] = Field(None, ge=0)
    workout_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class HealthLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    log_type: str
    calories: Optional[int]
    duration: Optional[int]
    description: Optional[str]
    food_name: Optional[str]
    protein: Optional[int]
    carbs: Optional[int]
    fat: Optional[int]
    workout_type: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HealthLogListResponse(BaseModel):
    logs: list[HealthLogResponse]
    total: int


class HealthStatsResponse(BaseModel):
    total_meals: int
    total_workouts: int
    total_calories: int
    total_workout_minutes: int


class DailyStatsResponse(BaseModel):
    calories_consumed: int
    calories_burned: int
    net_calories: int
