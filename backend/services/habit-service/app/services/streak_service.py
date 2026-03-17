"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Streak calculation service for the Habit Service.
"""

from uuid import UUID

from app.repositories.habit_log_repository import HabitLogRepository


class StreakService:
    """Service for calculating habit streaks."""

    def __init__(self, log_repo: HabitLogRepository):
        self.log_repo = log_repo

    async def get_current_streak(self, habit_id: UUID) -> int:
        """Get the current consecutive-day streak for a habit."""
        return await self.log_repo.get_streak(habit_id)

    async def get_longest_streak(self, habit_id: UUID) -> int:
        """Get the longest consecutive-day streak ever achieved."""
        return await self.log_repo.get_longest_streak(habit_id)
