"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Repository — data access layer for daily snapshots.
"""

from datetime import date
from uuid import UUID

from app.models.dashboard_model import DailySnapshot
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class DashboardRepository:
    """Data access layer for dashboard snapshots."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_snapshot(
        self, user_id: UUID, snapshot_date: date
    ) -> DailySnapshot | None:
        """Fetch a snapshot for a specific user and date."""
        result = await self.session.execute(
            select(DailySnapshot).where(
                (DailySnapshot.user_id == str(user_id))
                & (DailySnapshot.snapshot_date == snapshot_date.isoformat())
            )
        )
        return result.scalar_one_or_none()

    async def upsert_snapshot(
        self,
        user_id: UUID,
        snapshot_date: date,
        habits_completed: int = 0,
        total_habits: int = 0,
        learning_minutes: int = 0,
        calories_consumed: int = 0,
        calories_burned: int = 0,
        net_calories: int = 0,
        productivity_score: int = 0,
        notes_created_today: int = 0,
        records_created_today: int = 0,
        current_streak: int = 0,
    ) -> DailySnapshot:
        """
        Insert or update a snapshot.

        Uses PostgreSQL ON CONFLICT ... DO UPDATE (upsert) pattern.
        """
        snapshot_date_iso = snapshot_date.isoformat()
        values = dict(
            habits_completed=habits_completed,
            total_habits=total_habits,
            learning_minutes=learning_minutes,
            calories_consumed=calories_consumed,
            calories_burned=calories_burned,
            net_calories=net_calories,
            productivity_score=productivity_score,
            notes_created_today=notes_created_today,
            records_created_today=records_created_today,
            current_streak=current_streak,
        )

        existing = await self.get_snapshot(user_id, snapshot_date)
        if existing:
            await self.session.execute(
                update(DailySnapshot)
                .where(
                    (DailySnapshot.user_id == str(user_id))
                    & (DailySnapshot.snapshot_date == snapshot_date_iso)
                )
                .values(**values)
            )
        else:
            self.session.add(
                DailySnapshot(
                    user_id=str(user_id),
                    snapshot_date=snapshot_date_iso,
                    **values,
                )
            )
        await self.session.flush()

        # Fetch and return the updated/inserted snapshot
        return await self.get_snapshot(user_id, snapshot_date)

    async def get_weekly_snapshots(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[DailySnapshot]:
        """Fetch snapshots for a date range."""
        result = await self.session.execute(
            select(DailySnapshot)
            .where(
                (DailySnapshot.user_id == str(user_id))
                & (DailySnapshot.snapshot_date >= start_date.isoformat())
                & (DailySnapshot.snapshot_date <= end_date.isoformat())
            )
            .order_by(DailySnapshot.snapshot_date.asc())
        )
        return list(result.scalars().all())
