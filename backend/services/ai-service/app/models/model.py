"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM model for the AI Service.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.base_model import Base, TimestampMixin


class AIInteraction(Base, TimestampMixin):
    """AI interactions — stores AI recommendation requests and results."""

    __tablename__ = "ai_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    interaction_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="recommendation, summary, assistant"
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=True, default="")
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
