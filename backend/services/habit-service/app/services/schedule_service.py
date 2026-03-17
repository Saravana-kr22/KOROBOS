"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Habit scheduling service for the Habit Service.
Determines which habits are due today based on frequency and day_of_week.
"""

from datetime import date, time
from typing import Optional
from uuid import UUID

from app.repositories.habit_log_repository import HabitLogRepository


class ScheduleService:
    """Service for habit scheduling and determining today's habits."""

    def __init__(self, log_repo: HabitLogRepository):
        self.log_repo = log_repo

    async def get_today_habits(self, user_id: UUID) -> list[dict]:
        """Get habits that are due today for the user.

        Returns list of {"habit_id", "name", "completed": bool}.

        Scheduling logic:
        - daily: always due
        - weekly: due if today's weekday is in days_of_week (comma-separated ints)
        - custom: due if today's weekday is in days_of_week
        """
        # Get all habits with their schedules
        habits_with_status = await self.log_repo.get_today_habits(user_id)

        result = []
        today = date.today()
        today_weekday = today.weekday()  # 0=Monday, 6=Sunday

        for habit, completed in habits_with_status:
            schedule = await self.log_repo.get_schedule(habit.id)

            # Determine if this habit is due today
            is_due_today = False

            if schedule is None or schedule.frequency == "daily":
                # No schedule or default to daily
                is_due_today = True
            elif schedule.frequency == "weekly":
                # Check if today's weekday is in the schedule
                if schedule.days_of_week:
                    weekdays = [
                        int(w.strip()) for w in schedule.days_of_week.split(",")
                    ]
                    is_due_today = today_weekday in weekdays
            elif schedule.frequency == "custom":
                # Custom schedule: check days_of_week
                if schedule.days_of_week:
                    weekdays = [
                        int(w.strip()) for w in schedule.days_of_week.split(",")
                    ]
                    is_due_today = today_weekday in weekdays

            if is_due_today:
                result.append(
                    {
                        "habit_id": str(habit.id),
                        "name": habit.name,
                        "completed": completed,
                    }
                )

        return result

    async def create_schedule(
        self,
        habit_id: UUID,
        frequency: str = "daily",
        days_of_week: Optional[str] = None,
        time_of_day: Optional[time] = None,
    ):
        """Create a schedule for a habit.

        Args:
            habit_id: The habit to schedule
            frequency: "daily", "weekly", or "custom"
            days_of_week: Comma-separated integers (0=Mon, 6=Sun) for weekly/custom
            time_of_day: Time for reminders (e.g., "09:00:00")
        """
        return await self.log_repo.create_schedule(
            habit_id, frequency, days_of_week, time_of_day
        )

    async def update_schedule(self, habit_id: UUID, **kwargs):
        """Update a habit's schedule."""
        schedule = await self.log_repo.get_schedule(habit_id)
        if schedule:
            return await self.log_repo.update_schedule(schedule, **kwargs)
        return None
