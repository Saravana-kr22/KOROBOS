"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Redis-backed rate limiter for the Health Service.

Sprint 10 §20: 50 health logs per user per minute.
Uses a sliding-window counter stored in Redis with a 60-second TTL.
Falls back gracefully (allows the request) when Redis is unavailable.
"""

from uuid import UUID

from fastapi import Header, HTTPException, Request


async def check_log_rate_limit(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> None:
    """Dependency: raise 429 if the user exceeds 50 health logs per minute."""
    user_id = UUID(x_user_id)
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return  # Redis unavailable — degrade gracefully

    key = f"rate:health:logs:{user_id}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)  # start the 60-second window
        if count > 50:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many health logs. Limit: 50 per minute.",
                },
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis error — allow the request rather than blocking the user
