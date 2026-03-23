"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from backend.shared.config.settings import get_settings

settings = get_settings()

# Algorithm defaults to HS256, but can be overridden via settings
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def _get_signing_key() -> str:
    """Get the appropriate signing key based on algorithm."""
    if ALGORITHM == "RS256":
        if not settings.jwt_private_key:
            raise ValueError(
                "RS256 algorithm requires jwt_private_key to be set in configuration"
            )
        return settings.jwt_private_key
    else:  # HS256
        if not settings.jwt_secret:
            raise ValueError(
                "HS256 algorithm requires jwt_secret to be set in configuration"
            )
        return settings.jwt_secret


def _get_verification_key() -> str:
    """Get the appropriate key for token verification."""
    if ALGORITHM == "RS256":
        if not settings.jwt_public_key:
            raise ValueError(
                "RS256 algorithm requires jwt_public_key to be set in configuration"
            )
        return settings.jwt_public_key
    else:  # HS256
        if not settings.jwt_secret:
            raise ValueError(
                "HS256 algorithm requires jwt_secret to be set in configuration"
            )
        return settings.jwt_secret


def create_access_token(
    user_id: str,
    email: str,
    roles: list[str] | None = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: Unique identifier of the authenticated user.
        email: User's email address.
        roles: Optional list of role strings (e.g. ["admin", "user"]).
        expires_delta: Custom expiration duration; defaults to 15 min.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "roles": roles or ["user"],
        "iat": now,
        "exp": expire,
    }

    signing_key = _get_signing_key()
    return jwt.encode(payload, signing_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded token payload dict with keys: sub, email, roles, iat, exp.

    Raises:
        ValueError: If the token is invalid, expired, or malformed.
    """
    try:
        verification_key = _get_verification_key()
        payload = jwt.decode(token, verification_key, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing 'sub' claim")
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def create_refresh_token(user_id: str) -> str:
    """
    Create a signed JWT refresh token with long expiration.

    Args:
        user_id: Unique identifier of the authenticated user.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": user_id,
        "token_type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expire,
    }

    signing_key = _get_signing_key()
    return jwt.encode(payload, signing_key, algorithm=ALGORITHM)


def verify_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT refresh token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded token payload dict with keys: sub, token_type, iat, exp.

    Raises:
        ValueError: If the token is invalid, expired, or not a refresh token.
    """
    try:
        verification_key = _get_verification_key()
        payload = jwt.decode(token, verification_key, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")

        if user_id is None:
            raise ValueError("Token missing 'sub' claim")

        if token_type != "refresh":
            raise ValueError("Invalid token type; expected 'refresh'")

        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid refresh token: {exc}") from exc
