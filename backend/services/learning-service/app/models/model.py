"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Learning Service.
"""

import uuid

from backend.shared.database.base_model import Base, TimestampMixin
from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class LearningSession(Base, TimestampMixin):
    """Learning sessions table — tracks study/learning time."""

    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    duration: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Duration in minutes"
    )
    notes: Mapped[str] = mapped_column(Text, nullable=True, default="")
