"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Business logic for the Habit Service.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from app.events.events import (
    HabitCompletedEvent,
    HabitCreatedEvent,
    HabitStreakUpdatedEvent,
)
from app.models.model import Habit
from app.repositories.habit_log_repository import HabitLogRepository
from app.repositories.repository import HabitRepository
from app.schemas.schema import HabitCreate, HabitUpdate
from app.services.schedule_service import ScheduleService
from app.services.streak_service import StreakService
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.messaging.producer import publish_event


class HabitService:
    """Core business logic for Habit Service."""

    def __init__(self, session: AsyncSession):
        self.repo = HabitRepository(session)
        self.log_repo = HabitLogRepository(session)
        self.streak_service = StreakService(self.log_repo)
        self.schedule_service = ScheduleService(self.log_repo)

    async def create_habit(self, user_id: UUID, data: HabitCreate) -> Habit:
        habit = await self.repo.create(
            user_id=user_id,
            name=data.name,
            frequency=data.frequency,
            description=data.description or "",
        )

        # Create default schedule
        await self.schedule_service.create_schedule(
            habit.id,
            frequency=data.frequency,
            days_of_week=data.days_of_week,
            time_of_day=data.time_of_day,
        )

        event = HabitCreatedEvent(
            payload={
                "habit_id": str(habit.id),
                "user_id": str(user_id),
                "name": habit.name,
            }
        )
        await publish_event(event, key=str(user_id))
        return habit

    async def complete_habit(self, habit_id: UUID) -> tuple[bool, int]:
        habit = await self.repo.get_by_id(habit_id)
        if habit is None:
            return False, 0

        await self.log_repo.log_completion(habit_id, date.today())
        streak = await self.streak_service.get_current_streak(habit_id)
        event = HabitCompletedEvent(
            payload={
                "habit_id": str(habit_id),
                "user_id": str(habit.user_id),
                "streak": streak,
            }
        )
        await publish_event(event, key=str(habit.user_id))

        streak_event = HabitStreakUpdatedEvent(
            payload={
                "habit_id": str(habit_id),
                "user_id": str(habit.user_id),
                "streak": streak,
            }
        )
        await publish_event(streak_event, key=str(habit.user_id))
        return True, streak

    async def get_habit(self, habit_id: UUID) -> Optional[Habit]:
        return await self.repo.get_by_id(habit_id)

    async def list_habits(self, user_id: UUID, offset: int = 0, limit: int = 50):
        return await self.repo.list_by_user(user_id, offset, limit)

    async def update_habit(self, habit: Habit, data: HabitUpdate) -> Habit:
        return await self.repo.update(habit, **data.model_dump(exclude_unset=True))

    async def delete_habit(self, habit: Habit) -> None:
        await self.repo.delete(habit)

    async def get_today_habits(self, user_id: UUID) -> list[dict]:
        """Return today's habits (based on schedule) with completion status."""
        return await self.schedule_service.get_today_habits(user_id)

    async def get_stats(self, habit_id: UUID) -> dict:
        """Return habit analytics metrics."""
        stats = await self.log_repo.get_stats(habit_id)
        return {"habit_id": habit_id, **stats}

    async def get_user_habit_stats(self, user_id: UUID) -> dict:
        """Return aggregate habit statistics for user today."""
        habits, _ = await self.repo.list_by_user(user_id, offset=0, limit=1000)
        if not habits:
            return {
                "total_habits": 0,
                "habits_completed": 0,
                "current_streak": 0,
            }

        # Get today's habits with completion status
        today_habits = await self.get_today_habits(user_id)
        completed_count = sum(1 for h in today_habits if h.get("completed"))

        # Get max current streak across all habits
        max_streak = 0
        for habit in habits:
            if habit.is_active:
                streak = await self.streak_service.get_current_streak(habit.id)
                max_streak = max(max_streak, streak)

        return {
            "total_habits": len(habits),
            "habits_completed": completed_count,
            "current_streak": max_streak,
        }
