"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM model for the Notification Service.
"""

import uuid

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.base_model import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """Notifications table — in-app notifications and reminders."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    channel: Mapped[str] = mapped_column(
        String(50), nullable=False, default="in_app", comment="in_app, email, push"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PushToken(Base):
    """Push notification tokens for mobile devices."""

    __tablename__ = "push_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_token"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="ios, android"
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False)
