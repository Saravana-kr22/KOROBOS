"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for AI Insights and Recommendations.
"""

import uuid

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.base_model import Base, TimestampMixin


class AIInsight(Base, TimestampMixin):
    """AI Insights — stores generated insights per user."""

    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    insight_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="behavioral, performance, health, knowledge",
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0, comment="0.0 to 1.0"
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)


class AIRecommendation(Base, TimestampMixin):
    """AI Recommendations — stores generated recommendations per user."""

    __tablename__ = "ai_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="habit, learning, health, productivity",
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", comment="high, medium, low"
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
