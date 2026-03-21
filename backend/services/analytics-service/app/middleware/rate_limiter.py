"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Rate limiting middleware for analytics service.
Implements per-user rate limiting: 100 requests/minute/user
"""

import time
from typing import Optional

import redis
from fastapi import Request
from starlette.responses import JSONResponse


class RedisRateLimiter:
    """Redis-backed rate limiter for per-user request throttling."""

    def __init__(self, redis_client: redis.Redis, requests_per_minute: int = 100):
        """Initialize rate limiter.

        Args:
            redis_client: Redis connection
            requests_per_minute: Limit (default 100 req/min/user)
        """
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60

    async def check_rate_limit(self, user_id: str) -> tuple[bool, Optional[dict]]:
        """Check if user has exceeded rate limit.

        Returns:
            (allowed: bool, rate_info: dict with remaining/reset_in)
        """
        if not user_id:
            return True, None

        try:
            key = f"rate_limit:{user_id}"
            now = int(time.time())
            window_start = now - self.window_seconds

            # Remove old requests outside the window
            self.redis.zremrangebyscore(key, "-inf", window_start)

            # Count requests in current window
            request_count = self.redis.zcard(key)

            if request_count >= self.requests_per_minute:
                # Get oldest request timestamp to calculate reset time
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                reset_in = (
                    int(oldest[0][1]) + self.window_seconds - now
                    if oldest
                    else self.window_seconds
                )

                return False, {
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset_in_seconds": max(1, reset_in),
                }

            # Add current request
            self.redis.zadd(key, {str(now): now})

            # Set expiry on the key (window + 1 second buffer)
            self.redis.expire(key, self.window_seconds + 1)

            return True, {
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute - request_count - 1,
                "reset_in_seconds": self.window_seconds,
            }

        except Exception as e:
            # On Redis failure, allow request (fail open)
            print(f"Rate limiter error: {e}")
            return True, None


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting.

    Extracts user_id from X-User-ID header and checks rate limit.
    """
    # Get rate limiter from app state
    rate_limiter: Optional[RedisRateLimiter] = getattr(
        request.app.state, "rate_limiter", None
    )

    if rate_limiter:
        user_id = request.headers.get("X-User-ID")
        allowed, rate_info = await rate_limiter.check_rate_limit(user_id)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded: "
                        f"{rate_info['limit']} requests/minute",
                        "retry_after_seconds": rate_info["reset_in_seconds"],
                    },
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(time.time()) + rate_info["reset_in_seconds"]
                    ),
                    "Retry-After": str(rate_info["reset_in_seconds"]),
                },
            )

        # Add rate info to response headers
        response = await call_next(request)
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time()) + rate_info["reset_in_seconds"]
            )
        return response

    return await call_next(request)
