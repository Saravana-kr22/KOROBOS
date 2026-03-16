"""
KOROBOS — Database Service Rate Limiting

Rate limit enforcement for write operations.
"""

import logging
from uuid import UUID

from fastapi import Request
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)

# Rate limit: 30 writes per minute per user
WRITE_RATE_LIMIT = 30
RATE_LIMIT_WINDOW = 60  # seconds


async def check_write_rate_limit(
    request: Request,
    user_id: UUID,
) -> None:
    """Check if user has exceeded write rate limit.

    Uses Redis sliding-window counter. Falls back gracefully if Redis
    is unavailable.

    Args:
        request: FastAPI request (has app.state.redis)
        user_id: User ID

    Raises:
        HTTPException: 429 Too Many Requests if limit exceeded
    """
    redis = request.app.state.redis
    if not redis:
        logger.debug("Redis unavailable, skipping rate limit check")
        return

    key = f"rate:database:writes:{user_id}"

    try:
        # Increment counter
        count = await redis.incr(key)

        # Set expiry on first increment
        if count == 1:
            await redis.expire(key, RATE_LIMIT_WINDOW)

        # Check limit
        if count > WRITE_RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for user {user_id}: {count} writes")
            raise HTTPException(
                status_code=429,
                detail="Too many write requests. Try again later.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        # Graceful degradation — allow request if Redis fails
