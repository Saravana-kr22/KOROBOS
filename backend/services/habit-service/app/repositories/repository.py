"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for the Habit Service.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Habit, HabitLog


class HabitRepository:
    """Repository for Habit CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, name: str, frequency: str, description: str = "") -> Habit:
        habit = Habit(user_id=user_id, name=name, frequency=frequency, description=description)
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def get_by_id(self, habit_id: UUID) -> Optional[Habit]:
        result = await self.session.execute(select(Habit).where(Habit.id == habit_id))
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> tuple[list[Habit], int]:
        count_q = select(func.count()).select_from(Habit).where(Habit.user_id == user_id)
        total = (await self.session.execute(count_q)).scalar_one()
        q = select(Habit).where(Habit.user_id == user_id).order_by(Habit.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update(self, habit: Habit, **kwargs) -> Habit:
        for key, value in kwargs.items():
            if value is not None:
                setattr(habit, key, value)
        await self.session.flush()
        return habit

    async def delete(self, habit: Habit) -> None:
        await self.session.delete(habit)
        await self.session.flush()

    async def log_completion(self, habit_id: UUID, log_date: date) -> HabitLog:
        log = HabitLog(habit_id=habit_id, log_date=log_date, completed=True)
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_streak(self, habit_id: UUID) -> int:
        """Calculate current streak of consecutive completions."""
        q = (
            select(HabitLog)
            .where(HabitLog.habit_id == habit_id, HabitLog.completed.is_(True))
            .order_by(HabitLog.log_date.desc())
        )
        result = await self.session.execute(q)
        logs = result.scalars().all()

        streak = 0
        today = date.today()
        expected = today
        for log in logs:
            if log.log_date == expected:
                streak += 1
                from datetime import timedelta
                expected -= timedelta(days=1)
            else:
                break
        return streak
