"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.shared.config.settings import get_settings
from jose import JWTError, jwt

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(
    user_id: str,
    roles: list[str] | None = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        user_id: Unique identifier of the authenticated user.
        roles: Optional list of role strings (e.g. ["admin", "user"]).
        expires_delta: Custom expiration duration; defaults to 60 min.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: dict[str, Any] = {
        "sub": user_id,
        "roles": roles or ["user"],
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Decoded token payload dict with keys: sub, roles, iat, exp.

    Raises:
        ValueError: If the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing 'sub' claim")
        return payload
    except JWTError as exc:
        raise ValueError(f"Invalid token: {exc}") from exc
