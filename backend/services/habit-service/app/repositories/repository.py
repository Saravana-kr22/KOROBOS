"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for the Habit Service.
"""

from typing import Optional
from uuid import UUID

from app.models.model import Habit
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class HabitRepository:
    """Repository for Habit CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        name: str,
        frequency: str,
        description: str = "",
    ) -> Habit:
        habit = Habit(
            user_id=user_id,
            name=name,
            frequency=frequency,
            description=description,
        )
        self.session.add(habit)
        await self.session.flush()
        return habit

    async def get_by_id(self, habit_id: UUID) -> Optional[Habit]:
        result = await self.session.execute(select(Habit).where(Habit.id == habit_id))
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Habit], int]:
        count_q = (
            select(func.count()).select_from(Habit).where(Habit.user_id == user_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()
        q = (
            select(Habit)
            .where(Habit.user_id == user_id)
            .order_by(Habit.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
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
