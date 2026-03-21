"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard rate limiting via Redis sliding window counter.
"""

from uuid import UUID

from fastapi import Header, HTTPException, Request


async def check_dashboard_rate_limit(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> None:
    """
    Check rate limit for dashboard requests.

    Limit: 100 requests per 60 seconds per user (Sprint 11 §18).
    Uses Redis sliding window counter with graceful fallback.

    Raises:
        HTTPException: 429 Too Many Requests if limit exceeded.
    """
    user_id = UUID(x_user_id)
    redis = getattr(request.app.state, "redis", None)

    if redis is None:
        # No Redis — allow the request
        return

    key = f"rate:dashboard:{user_id}"

    try:
        count = await redis.incr(key)
        if count == 1:
            # First request in this window — set expiration
            await redis.expire(key, 60)

        if count > 100:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many dashboard requests. Limit: 100 per minute.",
                },
            )
    except HTTPException:
        raise
    except Exception:
        # Redis error — gracefully degrade and allow the request
        pass
