"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Service-to-Service Authentication Middleware for the API Gateway.
Validates service tokens from internal microservices.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from backend.shared.auth.service_token import verify_internal_service_token

logger = logging.getLogger("api-gateway.service-auth")


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates service-to-service authentication.

    - Checks for X-Service-Token header on protected inter-service paths.
    - Validates the token and injects service_id into request.state.
    - Allows services to call other services securely.
    """

    # Paths that require service authentication
    SERVICE_PATHS = [
        "/api/v1/auth/service",  # Only internal calls to auth service
        "/api/v1/notes/sync",  # Internal sync endpoints
        "/api/v1/habits/sync",  # Internal sync endpoints
        # Add more service paths as needed
    ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip if not a service path
        if not self._is_service_path(path):
            return await call_next(request)

        # Extract service token
        service_token = request.headers.get("X-Service-Token")
        if not service_token:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "MISSING_SERVICE_TOKEN",
                        "message": (
                            "X-Service-Token header required for inter-service calls"
                        ),
                    },
                },
            )

        # Extract service ID from token
        service_id = request.headers.get("X-Service-ID")
        if not service_id:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "MISSING_SERVICE_ID",
                        "message": "X-Service-ID header is required",
                    },
                },
            )

        try:
            # Verify token
            verify_internal_service_token(service_token, service_id)

            # Inject service context into request state
            request.state.service_id = service_id
            request.state.is_service_call = True

            logger.debug(f"Service {service_id} authenticated successfully")

        except ValueError as exc:
            logger.warning(
                f"Service auth failed for {service_id}: {exc}",
                extra={"path": path, "service": service_id},
            )
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_SERVICE_TOKEN",
                        "message": "Invalid or expired service token",
                    },
                },
            )

        return await call_next(request)

    @staticmethod
    def _is_service_path(path: str) -> bool:
        """Check if path requires service authentication."""
        for service_path in ServiceAuthMiddleware.SERVICE_PATHS:
            if path == service_path or path.startswith(service_path + "/"):
                return True
        return False
