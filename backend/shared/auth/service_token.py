"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Service-to-Service Authentication Token Management.
Allows microservices to authenticate with each other using service tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from backend.shared.config.settings import get_settings

settings = get_settings()

SERVICE_TOKEN_EXPIRE_HOURS = 24


def create_service_token(
    service_id: str,
    service_secret: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed service-to-service authentication token.

    Args:
        service_id: Unique identifier of the calling service
            (e.g., "auth-service", "notes-service").
        service_secret: Secret key provided for the service
            (from service registry).
        expires_delta: Custom expiration duration; defaults to 24 hours.

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If configuration is invalid.
    """
    if not settings.jwt_secret:
        raise ValueError("JWT secret not configured")

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(hours=SERVICE_TOKEN_EXPIRE_HOURS))

    payload: dict[str, Any] = {
        "service": service_id,
        "token_type": "service",
        "iat": now,
        "exp": expire,
    }

    # Sign with service secret + jwt_secret for added security
    combined_secret = f"{settings.jwt_secret}:{service_secret}"
    return jwt.encode(payload, combined_secret, algorithm="HS256")


def verify_service_token(
    token: str,
    service_id: str,
    service_secret: str,
) -> dict[str, Any]:
    """
    Verify a service-to-service token.

    Args:
        token: The service token to verify.
        service_id: Expected service identifier.
        service_secret: Service secret from registry.

    Returns:
        Decoded token payload.

    Raises:
        ValueError: If token is invalid, expired, or service doesn't match.
    """
    if not settings.jwt_secret:
        raise ValueError("JWT secret not configured")

    try:
        combined_secret = f"{settings.jwt_secret}:{service_secret}"
        payload = jwt.decode(token, combined_secret, algorithms=["HS256"])

        # Verify it's a service token
        token_type = payload.get("token_type")
        if token_type != "service":
            raise ValueError("Invalid token type; expected 'service'")

        # Verify service ID matches
        actual_service = payload.get("service")
        if actual_service != service_id:
            msg = f"Token service mismatch: {service_id} != {actual_service}"
            raise ValueError(msg)

        return payload

    except JWTError as exc:
        raise ValueError(f"Invalid service token: {exc}") from exc


def create_internal_service_token(service_id: str) -> str:
    """
    Create a service token using only the JWT secret (for internal/testing purposes).

    This is less secure than create_service_token and should only be used for
    internal service communication in development/testing.

    Args:
        service_id: Service identifier.

    Returns:
        Encoded JWT string.
    """
    if not settings.jwt_secret:
        raise ValueError("JWT secret not configured")

    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=SERVICE_TOKEN_EXPIRE_HOURS)

    payload: dict[str, Any] = {
        "service": service_id,
        "token_type": "service",
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_internal_service_token(token: str, service_id: str) -> dict[str, Any]:
    """
    Verify an internal service token (using only JWT secret).

    Args:
        token: The service token.
        service_id: Expected service identifier.

    Returns:
        Decoded payload.

    Raises:
        ValueError: If invalid or expired.
    """
    if not settings.jwt_secret:
        raise ValueError("JWT secret not configured")

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])

        token_type = payload.get("token_type")
        if token_type != "service":
            raise ValueError("Invalid token type; expected 'service'")

        actual_service = payload.get("service")
        if actual_service != service_id:
            msg = f"Token service mismatch: {service_id} != {actual_service}"
            raise ValueError(msg)

        return payload

    except JWTError as exc:
        raise ValueError(f"Invalid service token: {exc}") from exc
