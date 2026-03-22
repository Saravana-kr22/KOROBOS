"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for AI Insights and Recommendations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InsightResponse(BaseModel):
    """Insight response schema."""

    id: UUID
    user_id: UUID
    insight_type: str = Field(
        ..., description="behavioral, performance, health, knowledge"
    )
    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    """Recommendation response schema."""

    id: UUID
    user_id: UUID
    category: str = Field(..., description="habit, learning, health, productivity")
    text: str
    priority: str = Field(..., description="high, medium, low")
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsightListResponse(BaseModel):
    """List of insights with pagination."""

    insights: list[InsightResponse]
    total: int


class RecommendationListResponse(BaseModel):
    """List of recommendations with pagination."""

    recommendations: list[RecommendationResponse]
    total: int


class SummaryResponse(BaseModel):
    """Combined summary of insights and recommendations."""

    user_id: UUID
    summary: str = Field(..., description="Natural language summary from AI")
    generated_at: datetime
    insights: list[InsightResponse]
    recommendations: list[RecommendationResponse]
