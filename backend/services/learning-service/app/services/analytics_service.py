"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — dedicated module for learning analytics computation.

Provides the analytics interface consumed by API routes, keeping business
logic separated from the data access layer (repository).
"""

from uuid import UUID

from app.repositories.session_repository import LearningRepository
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsService:
    """Computes learning analytics metrics for a user."""

    def __init__(self, session: AsyncSession):
        self.repo = LearningRepository(session)

    async def get_stats(self, user_id: UUID) -> dict:
        """
        Return enhanced learning statistics:
          - total_sessions
          - total_minutes
          - topics (distinct list)
          - sessions_today
          - current_streak (consecutive days)
          - weekly_minutes (last 7 days)
          - topic_distribution (topic → total minutes)
        """
        return await self.repo.get_stats(user_id)

    async def get_topic_distribution(self, user_id: UUID) -> dict[str, int]:
        """Return mapping of topic name → total minutes studied."""
        stats = await self.repo.get_stats(user_id)
        return stats["topic_distribution"]

    async def get_streak(self, user_id: UUID) -> int:
        """Return the current consecutive-day learning streak."""
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).date()
        return await self.repo._calculate_streak(user_id, today)

    async def get_weekly_minutes(self, user_id: UUID) -> int:
        """Return total minutes studied in the last 7 days."""
        stats = await self.repo.get_stats(user_id)
        return stats["weekly_minutes"]
