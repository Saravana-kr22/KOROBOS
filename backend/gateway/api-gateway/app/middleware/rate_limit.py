"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Redis-backed Rate Limiting Middleware for the API Gateway.
Uses sliding-window counters per user and per IP.
"""

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config.gateway_settings import get_gateway_settings

logger = logging.getLogger("api-gateway.ratelimit")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed rate limiter.

    Policy:
        - Authenticated users: `rate_limit_per_user` requests/min (keyed by user_id)
        - Unauthenticated requests: `rate_limit_per_ip` requests/min (keyed by IP)

    Gracefully degrades if Redis is unavailable — requests are allowed through.
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_gateway_settings()

        # Skip rate limiting on health/docs
        path = request.url.path
        if path in ("/health", "/metrics", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        # Determine rate limit key and ceiling
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"rl:user:{user_id}"
            limit = settings.rate_limit_per_user
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"rl:ip:{client_ip}"
            limit = settings.rate_limit_per_ip

        # Check rate limit via Redis
        if self.redis is not None:
            try:
                is_allowed = await self._check_rate_limit(key, limit)
                if not is_allowed:
                    logger.warning(f"Rate limit exceeded for {key}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "status": "error",
                            "error": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "message": "Too many requests. Please try again later.",
                            },
                        },
                    )
            except Exception as exc:
                # Graceful degradation: if Redis is down, allow requests
                logger.error(f"Rate limiter error (degraded mode): {exc}")

        return await call_next(request)

    async def _check_rate_limit(self, key: str, limit: int) -> bool:
        """
        Sliding-window counter using Redis.

        Returns True if the request is allowed, False if rate limit is exceeded.
        """
        now = int(time.time())
        window_key = f"{key}:{now // 60}"  # 1-minute window

        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, 120)  # TTL 2 minutes for safety
        results = await pipe.execute()

        current_count = results[0]
        return current_count <= limit
