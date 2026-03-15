"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Redis-backed rate limiter for the Notes Service.

Sprint 6 §21: 50 note write operations per user per minute.
Uses a sliding-window counter stored in Redis with a 60-second TTL.
Falls back gracefully (allows the request) when Redis is unavailable.
"""

from uuid import UUID

from fastapi import HTTPException, Request


async def _redis_from_request(request: Request):
    """Retrieve the shared Redis client from app state (may be None)."""
    return getattr(request.app.state, "redis", None)


async def check_write_rate_limit(request: Request, user_id: UUID) -> None:
    """Dependency: raise 429 if the user exceeds 50 write ops/minute."""
    redis = await _redis_from_request(request)
    if redis is None:
        return  # Redis unavailable — degrade gracefully

    key = f"rate:notes:writes:{user_id}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)  # start the 60-second window
        if count > 50:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many note write operations. Limit: 50 per minute.",
                },
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Redis error — allow the request rather than blocking the user
