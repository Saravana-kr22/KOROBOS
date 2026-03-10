"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Business logic for the Habit Service.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from app.events.events import HabitCompletedEvent, HabitCreatedEvent
from app.models.model import Habit
from app.repositories.repository import HabitRepository
from app.schemas.schema import HabitCreate, HabitUpdate
from backend.shared.messaging.producer import publish_event
from sqlalchemy.ext.asyncio import AsyncSession


class HabitService:
    """Core business logic for Habit Service."""

    def __init__(self, session: AsyncSession):
        self.repo = HabitRepository(session)

    async def create_habit(self, user_id: UUID, data: HabitCreate) -> Habit:
        habit = await self.repo.create(
            user_id=user_id,
            name=data.name,
            frequency=data.frequency,
            description=data.description or "",
        )
        event = HabitCreatedEvent(
            payload={
                "habit_id": str(habit.id),
                "user_id": str(user_id),
            }
        )
        await publish_event(event, key=str(user_id))
        return habit

    async def complete_habit(self, habit_id: UUID) -> tuple[bool, int]:
        habit = await self.repo.get_by_id(habit_id)
        if habit is None:
            return False, 0

        await self.repo.log_completion(habit_id, date.today())
        streak = await self.repo.get_streak(habit_id)
        event = HabitCompletedEvent(
            payload={
                "habit_id": str(habit_id),
                "user_id": str(habit.user_id),
                "streak": streak,
            }
        )
        await publish_event(event, key=str(habit.user_id))
        return True, streak

    async def get_habit(self, habit_id: UUID) -> Optional[Habit]:
        return await self.repo.get_by_id(habit_id)

    async def list_habits(self, user_id: UUID, offset: int = 0, limit: int = 50):
        return await self.repo.list_by_user(user_id, offset, limit)

    async def update_habit(self, habit: Habit, data: HabitUpdate) -> Habit:
        return await self.repo.update(habit, **data.model_dump(exclude_unset=True))

    async def delete_habit(self, habit: Habit) -> None:
        await self.repo.delete(habit)
