"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM model for the Analytics Service.
"""

import uuid

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.base_model import Base, TimestampMixin


class AnalyticsMetric(Base, TimestampMixin):
    """Analytics metrics — stores computed productivity scores and trends."""

    __tablename__ = "analytics_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="e.g. productivity_score, habit_consistency",
    )
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
