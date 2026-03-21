"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

LearningSession and SessionNote ORM models for the Learning Service.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.topic_model import Topic


class LearningSession(Base, TimestampMixin):
    """Learning sessions table — tracks study/learning time."""

    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # Free-text topic name (used for manual logs and display)
    topic: Mapped[str] = mapped_column(String(300), nullable=False)
    # Optional FK to a managed Topic entity
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    duration: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Duration in minutes"
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Session lifecycle: active | paused | completed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    topic_rel: Mapped[Optional["Topic"]] = relationship(
        back_populates="sessions", lazy="selectin"
    )
    session_notes: Mapped[list["SessionNote"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class SessionNote(Base):
    """Join table linking learning sessions to notes (knowledge system)."""

    __tablename__ = "session_notes"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
