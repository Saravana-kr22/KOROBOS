"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM model for the NoteLink entity.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base


class NoteLink(Base):
    __tablename__ = "note_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    target_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )

    source_note: Mapped["Note"] = relationship(  # noqa: F821
        foreign_keys=[source_note_id], back_populates="outgoing_links"
    )
    target_note: Mapped["Note"] = relationship(  # noqa: F821
        foreign_keys=[target_note_id]
    )
