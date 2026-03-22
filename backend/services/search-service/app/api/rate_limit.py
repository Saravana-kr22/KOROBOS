"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Rate Limiter — Redis-backed sliding window rate limiting.
"""

import redis.asyncio as aioredis

from backend.shared.logging.logger import get_logger

logger = get_logger("search-service.rate_limit")


class RateLimiter:
    """Redis-backed sliding window rate limiter."""

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def is_allowed(
        self, user_id: str, operation: str, limit_per_minute: int
    ) -> bool:
        """
        Check if a user has remaining quota for an operation.

        Args:
            user_id: User identifier
            operation: Operation name (e.g., 'search', 'write')
            limit_per_minute: Max requests allowed per minute

        Returns:
            True if request is allowed, False if rate limit exceeded.
        """
        key = f"rate:{operation}:{user_id}"

        try:
            current = await self.redis.incr(key)
            if current == 1:
                # First request, set expiry
                await self.redis.expire(key, 60)

            if current > limit_per_minute:
                logger.debug(
                    f"Rate limit exceeded for {user_id} on {operation}: "
                    f"{current}/{limit_per_minute}"
                )
                return False

            return True
        except Exception as exc:
            logger.warning(f"Rate limiter error: {exc}, allowing request")
            return True  # Degrade gracefully
