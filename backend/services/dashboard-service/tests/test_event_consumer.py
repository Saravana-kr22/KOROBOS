"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for Dashboard cache invalidation event consumer.
"""

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.events.event_consumer import DashboardCacheConsumer


@pytest.mark.asyncio
class TestDashboardCacheConsumer:
    """Test DashboardCacheConsumer cache invalidation logic."""

    async def test_cache_invalidation_on_habit_completed(self):
        """Consumer deletes correct cache keys on habit.completed event."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=3)  # 3 keys deleted

        consumer = DashboardCacheConsumer(redis=mock_redis)
        user_id = str(uuid4())
        today = date.today().isoformat()
        week_num = date.today().isocalendar()[1]

        await consumer.handle_event(
            "habit.completed",
            {"user_id": user_id, "habit_id": str(uuid4())},
        )

        # Verify delete was called with correct cache keys
        mock_redis.delete.assert_called_once()
        call_args = mock_redis.delete.call_args[0]
        assert f"cache:dashboard:overview:{user_id}" in call_args
        assert f"cache:dashboard:daily:{user_id}:{today}" in call_args
        assert f"cache:dashboard:weekly:{user_id}:{week_num}" in call_args

    async def test_cache_invalidation_on_learning_completed(self):
        """Consumer invalidates cache on learning.session.completed event."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=3)

        consumer = DashboardCacheConsumer(redis=mock_redis)
        user_id = str(uuid4())

        await consumer.handle_event(
            "learning.session.completed",
            {
                "user_id": user_id,
                "session_id": str(uuid4()),
                "duration_minutes": 45,
            },
        )

        mock_redis.delete.assert_called_once()

    async def test_cache_invalidation_on_meal_logged(self):
        """Consumer invalidates cache on meal.logged event."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=3)

        consumer = DashboardCacheConsumer(redis=mock_redis)
        user_id = str(uuid4())

        await consumer.handle_event(
            "meal.logged",
            {"user_id": user_id, "meal_id": str(uuid4()), "calories": 500},
        )

        mock_redis.delete.assert_called_once()

    async def test_cache_invalidation_on_workout_logged(self):
        """Consumer invalidates cache on workout.logged event."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=3)

        consumer = DashboardCacheConsumer(redis=mock_redis)
        user_id = str(uuid4())

        await consumer.handle_event(
            "workout.logged",
            {
                "user_id": user_id,
                "workout_id": str(uuid4()),
                "calories_burned": 300,
            },
        )

        mock_redis.delete.assert_called_once()

    async def test_cache_invalidation_ignores_missing_user_id(self):
        """Consumer skips cache invalidation if user_id missing from payload."""
        mock_redis = AsyncMock()

        consumer = DashboardCacheConsumer(redis=mock_redis)

        await consumer.handle_event(
            "habit.completed",
            {"habit_id": str(uuid4())},  # No user_id
        )

        # Redis delete should NOT be called
        mock_redis.delete.assert_not_called()

    async def test_cache_invalidation_noop_without_redis(self):
        """Consumer gracefully skips invalidation if Redis is None."""
        consumer = DashboardCacheConsumer(redis=None)
        user_id = str(uuid4())

        # Should not raise an exception
        await consumer.handle_event(
            "habit.completed",
            {"user_id": user_id},
        )

    async def test_cache_invalidation_handles_redis_error(self):
        """Consumer handles Redis errors gracefully."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis connection lost"))

        consumer = DashboardCacheConsumer(redis=mock_redis)
        user_id = str(uuid4())

        # Should not raise an exception
        await consumer.handle_event(
            "habit.completed",
            {"user_id": user_id},
        )

        # Delete should have been attempted
        mock_redis.delete.assert_called_once()
