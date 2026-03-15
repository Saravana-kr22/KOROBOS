"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM model for the Note entity.
"""

import uuid

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin


class Note(Base, TimestampMixin):
    """Notes table — stores markdown knowledge notes."""

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Resolved via string refs at mapper configuration time
    tags: Mapped[list["NoteTag"]] = relationship(  # noqa: F821
        back_populates="note",
        cascade="all, delete-orphan",
    )
    outgoing_links: Mapped[list["NoteLink"]] = relationship(  # noqa: F821
        foreign_keys="NoteLink.source_note_id",
        back_populates="source_note",
        cascade="all, delete-orphan",
    )
