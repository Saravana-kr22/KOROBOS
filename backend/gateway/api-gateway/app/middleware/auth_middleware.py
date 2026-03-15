"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

JWT Authentication Middleware for the API Gateway.
Validates Bearer tokens on every request except public paths.
"""

import logging

from app.config.gateway_settings import get_gateway_settings
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("api-gateway.auth")

ALGORITHM = "HS256"


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates JWT Bearer tokens.

    - Requests to public paths (health, docs, auth login/signup) are passed through.
    - All other requests must include a valid `Authorization: Bearer <token>` header.
    - On success, decoded `user_id` and `roles` are injected into `request.state`.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_gateway_settings()

        # Skip authentication for public paths
        path = request.url.path
        if self._is_public(path, settings.public_paths):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "MISSING_TOKEN",
                        "message": "Authorization header with Bearer token is required",
                    },
                },
            )

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise ValueError("Token missing 'sub' claim")

            # Inject user context into request state
            request.state.user_id = user_id
            request.state.roles = payload.get("roles", ["user"])

        except (JWTError, ValueError) as exc:
            logger.warning(f"Auth failed: {exc}", extra={"path": path})
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid or expired authentication token",
                    },
                },
            )

        return await call_next(request)

    @staticmethod
    def _is_public(path: str, public_paths: list[str]) -> bool:
        """Check if the request path matches any public path prefix."""
        for public in public_paths:
            if path == public or path.startswith(public + "/"):
                return True
        return False
