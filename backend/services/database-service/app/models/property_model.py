"""
KOROBOS — Database Service Property Model

Property/field definitions for structured databases.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base

if TYPE_CHECKING:
    from backend.services.database_service.app.models.database_model import Database
    from backend.services.database_service.app.models.record_model import RecordValue


class Property(Base):
    """Database property (field) definition.

    Defines a column in a structured database with type constraints
    and optional type-specific configuration (e.g., select choices).

    Properties do not have updated_at because they are replaced, not modified.
    """

    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    database_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("databases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.utcnow
    )

    # Relationships
    database: Mapped["Database"] = relationship(back_populates="properties")
    values: Mapped[list["RecordValue"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Property id={self.id} name={self.name} type={self.type}>"
