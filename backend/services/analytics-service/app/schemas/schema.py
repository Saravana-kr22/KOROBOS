"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MetricCreate(BaseModel):
    metric_type: str = Field(..., max_length=100)
    value: float
    metadata_json: Optional[dict[str, Any]] = None


class MetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    metric_type: str
    value: float
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductivityResponse(BaseModel):
    productivity_score: float
    habit_consistency: float
    learning_hours: float


class TrendResponse(BaseModel):
    metric_type: str
    values: list[float]
    labels: list[str]
