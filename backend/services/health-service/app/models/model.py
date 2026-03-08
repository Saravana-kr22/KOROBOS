"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Health Service.
"""

import uuid

from backend.shared.database.base_model import Base, TimestampMixin
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class HealthLog(Base, TimestampMixin):
    """Health logs — tracks meals, workouts, and health metrics."""

    __tablename__ = "health_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    log_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="meal or workout"
    )
    calories: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    duration: Mapped[int] = mapped_column(
        Integer, nullable=True, default=0, comment="Duration in minutes"
    )
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
