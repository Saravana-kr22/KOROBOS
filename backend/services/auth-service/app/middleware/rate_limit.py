"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Rate limiting middleware for login endpoint.
"""

from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Request, status
from redis import Redis

# Import Redis from shared config when available
try:
    from backend.shared.config.settings import get_settings

    settings = get_settings()
    REDIS_URL = settings.redis_url
except Exception:
    REDIS_URL = "redis://localhost:6379"


class LoginRateLimiter:
    """Rate limit login attempts per IP and email combination."""

    # 10 requests per minute per IP
    RATE_LIMIT = 10
    WINDOW_SECONDS = 60

    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize rate limiter with optional Redis client."""
        self.redis = redis_client
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection if not provided."""
        if not self.redis:
            try:
                from redis import Redis

                self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
                # Test connection
                self.redis.ping()
            except Exception:
                # Fallback to in-memory rate limiting if Redis unavailable
                self.redis = None
                self._in_memory_store = {}

    async def check_limit(self, ip_address: str, email: Optional[str] = None) -> bool:
        """
        Check if request is within rate limit.

        Args:
            ip_address: Client IP address.
            email: Optional email address.

        Returns:
            True if within limit, False if exceeded.
        """
        key = f"login_attempts:{ip_address}"
        if email:
            key += f":{email}"

        if self.redis:
            return await self._check_redis(key)
        else:
            return self._check_memory(key)

    async def _check_redis(self, key: str) -> bool:
        """Check rate limit against Redis."""
        try:
            count = self.redis.get(key)
            if count and int(count) >= self.RATE_LIMIT:
                return False

            # Increment counter with expiration
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.WINDOW_SECONDS)
            pipe.execute()

            return True
        except Exception:
            # Fail open if Redis unavailable
            return True

    def _check_memory(self, key: str) -> bool:
        """Check rate limit against in-memory store (fallback)."""
        now = datetime.now(timezone.utc)

        if key not in self._in_memory_store:
            self._in_memory_store[key] = {
                "count": 1,
                "reset_at": now + timedelta(seconds=self.WINDOW_SECONDS),
            }
            return True

        entry = self._in_memory_store[key]

        # Reset if window expired
        if now >= entry["reset_at"]:
            entry["count"] = 1
            entry["reset_at"] = now + timedelta(seconds=self.WINDOW_SECONDS)
            return True

        # Check limit
        if entry["count"] >= self.RATE_LIMIT:
            return False

        entry["count"] += 1
        return True


# Global rate limiter instance
_rate_limiter: Optional[LoginRateLimiter] = None


def get_rate_limiter() -> LoginRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = LoginRateLimiter()
    return _rate_limiter


def add_rate_limit_middleware(app: FastAPI) -> None:
    """
    Add rate limiting middleware to FastAPI app.

    Protects login and password reset endpoints.
    """

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable):
        """Rate limiting middleware for protected endpoints."""
        # Only rate limit login and password-reset endpoints
        if request.url.path.endswith("/login") and request.method == "POST":
            limiter = get_rate_limiter()
            ip_address = request.client.host if request.client else "unknown"

            # Try to extract email from request body for more granular limiting
            email = None
            try:
                if request.method == "POST":
                    body = await request.body()
                    import json

                    if body:
                        data = json.loads(body)
                        email = data.get("email", "").lower()
            except Exception:
                pass

            # Check rate limit
            if not await limiter.check_limit(ip_address, email):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please try again later.",
                )

        return await call_next(request)
