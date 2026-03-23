"""
KOROBOS — Database Service Models

Database model for structured database definitions.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.property_model import Property
    from app.models.record_model import Record


class Database(Base, TimestampMixin):
    """User-owned structured database definition.

    Contains the metadata for a custom database and references to its
    properties (fields) and records (rows).
    """

    __tablename__ = "databases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    properties: Mapped[list["Property"]] = relationship(
        back_populates="database",
        cascade="all, delete-orphan",
        order_by="Property.position",
    )
    records: Mapped[list["Record"]] = relationship(
        back_populates="database",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Database id={self.id} name={self.name}>"
