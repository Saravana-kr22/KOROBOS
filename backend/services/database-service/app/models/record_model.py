"""
KOROBOS — Database Service Record Models

Record and RecordValue models for EAV storage pattern.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.services.database_service.app.models.database_model import Database
    from backend.services.database_service.app.models.property_model import Property


class Record(Base, TimestampMixin):
    """Database record (row) within a structured database.

    Records store data related to a specific database and can optionally
    link to a note in the notes-service (soft reference, no cross-service FK).

    Actual field values are stored in the record_values table using EAV pattern.
    """

    __tablename__ = "records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("databases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    note_id: Mapped[Optional[uuid.UUID]] = mapped_column(index=True, nullable=True)

    # Relationships
    database: Mapped["Database"] = relationship(back_populates="records")
    values: Mapped[list["RecordValue"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Record id={self.id} database_id={self.database_id}>"


class RecordValue(Base):
    """Entity-Attribute-Value storage for record field values.

    Each record can have multiple values, one per property. Values are stored
    as TEXT and type casting is handled at the service layer.

    Uses composite primary key (record_id, property_id) to enforce one value
    per (record, property) pair.
    """

    __tablename__ = "record_values"
    __table_args__ = (PrimaryKeyConstraint("record_id", "property_id"),)

    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("records.id", ondelete="CASCADE"),
        nullable=False,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    record: Mapped["Record"] = relationship(back_populates="values")
    property: Mapped["Property"] = relationship(back_populates="values")

    def __repr__(self) -> str:
        return (
            f"<RecordValue record_id={self.record_id} "
            f"property_id={self.property_id} value={self.value}>"
        )
