"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service ORM models.
"""

from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.database.base_model import Base, TimestampMixin


class DailySnapshot(Base, TimestampMixin):
    """
    Materialized daily aggregate snapshot for a user.

    Stores pre-computed daily metrics (habits completed, learning minutes,
    calories, productivity score) for fast weekly/monthly trend queries.
    One snapshot per user per date (unique constraint enforced).
    """

    __tablename__ = "daily_snapshots"

    user_id: Mapped[str] = mapped_column(nullable=False, index=True)
    snapshot_date: Mapped[str] = mapped_column(nullable=False)  # ISO date string

    # Habit metrics
    habits_completed: Mapped[int] = mapped_column(default=0)
    total_habits: Mapped[int] = mapped_column(default=0)
    current_streak: Mapped[int] = mapped_column(default=0)

    # Learning metrics
    learning_minutes: Mapped[int] = mapped_column(default=0)

    # Health metrics
    calories_consumed: Mapped[int] = mapped_column(default=0)
    calories_burned: Mapped[int] = mapped_column(default=0)
    net_calories: Mapped[int] = mapped_column(default=0)

    # Computed metric
    productivity_score: Mapped[int] = mapped_column(default=0)

    # Notes and database activity metrics
    notes_created_today: Mapped[int] = mapped_column(default=0)
    records_created_today: Mapped[int] = mapped_column(default=0)
