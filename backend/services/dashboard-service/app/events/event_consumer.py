"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service — Kafka consumer for cache invalidation.
Listens to events from habit, learning, and health services
and invalidates relevant dashboard cache keys.
"""

import logging
from datetime import date

import redis.asyncio as aioredis

from backend.shared.messaging.consumer import BaseEventConsumer
from backend.workers.topics import DASHBOARD_TOPICS

logger = logging.getLogger(__name__)


class DashboardCacheConsumer(BaseEventConsumer):
    """
    Consumes dashboard-relevant events and invalidates Redis cache.

    Subscribes to:
    - habit.completed: clears user's dashboard cache
    - learning.session.completed: clears user's dashboard cache
    - meal.logged: clears user's dashboard cache
    - workout.logged: clears user's dashboard cache

    Cache keys invalidated:
    - cache:dashboard:overview:{user_id}
    - cache:dashboard:daily:{user_id}:{today_date}
    - cache:dashboard:weekly:{user_id}:{week_number}
    """

    topics = list(DASHBOARD_TOPICS)
    group_id = "dashboard-service"

    def __init__(self, redis: aioredis.Redis | None = None):
        super().__init__()
        self._redis = redis

    async def handle_event(self, topic: str, payload: dict) -> None:
        """
        Invalidate dashboard cache for the affected user.

        Args:
            topic: Event topic
            payload: Event payload containing at minimum user_id
        """
        # Skip if no Redis client
        if not self._redis:
            return

        # Extract user_id from payload
        user_id = payload.get("user_id")
        if not user_id:
            logger.warning(f"Cache invalidation skipped: no user_id in {topic} payload")
            return

        # Calculate cache keys
        today = date.today().isoformat()
        week_num = date.today().isocalendar()[1]
        keys_to_delete = [
            f"cache:dashboard:overview:{user_id}",
            f"cache:dashboard:daily:{user_id}:{today}",
            f"cache:dashboard:weekly:{user_id}:{week_num}",
        ]

        # Delete cache keys
        try:
            deleted_count = await self._redis.delete(*keys_to_delete)
            if deleted_count > 0:
                logger.debug(
                    f"Invalidated {deleted_count} dashboard cache "
                    f"key(s) for user {user_id} on {topic} event"
                )
        except Exception as exc:
            logger.error(
                f"Failed to invalidate dashboard cache for user {user_id}: {exc}"
            )
