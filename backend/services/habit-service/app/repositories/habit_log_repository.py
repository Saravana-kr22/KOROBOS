"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for Habit Logs and Schedules.
"""

from datetime import date, time, timedelta
from typing import Optional
from uuid import UUID

from app.models.model import Habit, HabitLog, HabitSchedule
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class HabitLogRepository:
    """Repository for habit logs, schedules, and analytics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_completion(self, habit_id: UUID, log_date: date) -> HabitLog:
        """Insert a habit completion log for a given date."""
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
                expected -= timedelta(days=1)
            else:
                break
        return streak

    async def get_longest_streak(self, habit_id: UUID) -> int:
        """Calculate longest consecutive streak ever achieved."""
        q = (
            select(HabitLog)
            .where(HabitLog.habit_id == habit_id, HabitLog.completed.is_(True))
            .order_by(HabitLog.log_date.asc())
        )
        result = await self.session.execute(q)
        logs = list(result.scalars().all())

        if not logs:
            return 0

        longest = 1
        current = 1
        for i in range(1, len(logs)):
            if logs[i].log_date - logs[i - 1].log_date == timedelta(days=1):
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        return longest

    async def get_stats(self, habit_id: UUID) -> dict:
        """Calculate habit statistics: completion rate, streaks, weekly consistency."""
        q = (
            select(HabitLog)
            .where(HabitLog.habit_id == habit_id, HabitLog.completed.is_(True))
            .order_by(HabitLog.log_date.asc())
        )
        result = await self.session.execute(q)
        logs = list(result.scalars().all())

        # Current and longest streak
        current_streak = await self.get_streak(habit_id)
        longest_streak = await self.get_longest_streak(habit_id)

        # Completion rate: count of completions / days since first log
        completion_rate = 0.0
        if logs:
            days_since_first = (date.today() - logs[0].log_date).days + 1
            completion_rate = len(logs) / max(days_since_first, 1)

        # Weekly consistency: completions in last 7 days / 7
        week_ago = date.today() - timedelta(days=6)
        week_q = (
            select(func.count())
            .select_from(HabitLog)
            .where(
                and_(
                    HabitLog.habit_id == habit_id,
                    HabitLog.log_date >= week_ago,
                    HabitLog.completed.is_(True),
                )
            )
        )
        weekly_count = (await self.session.execute(week_q)).scalar_one()
        weekly_consistency = weekly_count / 7.0

        return {
            "completion_rate": completion_rate,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "weekly_consistency": weekly_consistency,
        }

    async def get_today_habits(self, user_id: UUID) -> list[tuple[Habit, bool]]:
        """Get today's habits with completion status (for all active habits)."""
        q = (
            select(Habit)
            .where(Habit.user_id == user_id, Habit.is_active.is_(True))
            .order_by(Habit.created_at.desc())
        )
        result = await self.session.execute(q)
        habits = result.scalars().all()

        today = date.today()
        result_tuples = []
        for habit in habits:
            # Check if this habit was completed today
            log_q = (
                select(func.count())
                .select_from(HabitLog)
                .where(
                    and_(
                        HabitLog.habit_id == habit.id,
                        HabitLog.log_date == today,
                        HabitLog.completed.is_(True),
                    )
                )
            )
            completed = (await self.session.execute(log_q)).scalar_one() > 0
            result_tuples.append((habit, completed))

        return result_tuples

    async def get_schedule(self, habit_id: UUID) -> Optional[HabitSchedule]:
        """Get the schedule for a habit."""
        q = select(HabitSchedule).where(HabitSchedule.habit_id == habit_id)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def create_schedule(
        self,
        habit_id: UUID,
        frequency: str,
        days_of_week: Optional[str] = None,
        time_of_day: Optional[time] = None,
    ) -> HabitSchedule:
        """Create a schedule for a habit."""
        schedule = HabitSchedule(
            habit_id=habit_id,
            frequency=frequency,
            days_of_week=days_of_week,
            time_of_day=time_of_day,
        )
        self.session.add(schedule)
        await self.session.flush()
        return schedule

    async def update_schedule(self, schedule: HabitSchedule, **kwargs) -> HabitSchedule:
        """Update a habit schedule."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(schedule, key, value)
        await self.session.flush()
        return schedule

    async def has_completed_today(self, habit_id: UUID, log_date: date) -> bool:
        """Check if a habit was completed on a specific date."""
        q = (
            select(func.count())
            .select_from(HabitLog)
            .where(
                and_(
                    HabitLog.habit_id == habit_id,
                    HabitLog.log_date == log_date,
                    HabitLog.completed.is_(True),
                )
            )
        )
        count = (await self.session.execute(q)).scalar_one()
        return count > 0
