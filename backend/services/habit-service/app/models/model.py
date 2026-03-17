"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Habit Service.
"""

import uuid
from datetime import date, time
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin


class Habit(Base, TimestampMixin):
    """Habits table — tracks user habits."""

    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="daily")
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    logs: Mapped[list["HabitLog"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )
    schedule: Mapped[Optional["HabitSchedule"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan", uselist=False
    )


class HabitSchedule(Base, TimestampMixin):
    """Habit Schedules table — defines when habits should be completed."""

    __tablename__ = "habit_schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="daily")
    days_of_week: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    time_of_day: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    habit: Mapped["Habit"] = relationship(back_populates="schedule")


class HabitLog(Base):
    """Habit completion logs."""

    __tablename__ = "habit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    habit: Mapped["Habit"] = relationship(back_populates="logs")
