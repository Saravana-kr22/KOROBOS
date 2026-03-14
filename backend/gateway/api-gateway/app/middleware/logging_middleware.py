"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Request Logging Middleware for the API Gateway.
Emits structured JSON logs for every request/response cycle.
"""

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("api-gateway.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every request with structured JSON fields.

    Captured fields:
        - request_id (UUID)
        - method
        - path
        - status_code
        - latency_ms
        - client_ip
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        # Forward to next middleware / route handler
        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "client_ip": request.client.host if request.client else "unknown",
        }

        # Attach user_id if available from auth middleware
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            log_data["user_id"] = user_id

        if response.status_code >= 400:
            logger.warning("Request completed", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)

        # Inject request-id into response headers for tracing
        response.headers["X-Request-ID"] = request_id

        return response
