"""
Unit tests for the shared JWT handler.

Tests: create_access_token, verify_token — valid, expired, and invalid tokens.
"""

from datetime import timedelta

import pytest
from backend.shared.auth.jwt_handler import (
    create_access_token,
    verify_token,
)


class TestCreateAccessToken:
    """Tests for create_access_token."""

    def test_creates_valid_token(self):
        token = create_access_token(user_id="user-123", roles=["admin", "user"])
        assert isinstance(token, str)
        assert len(token) > 0

    def test_default_roles(self):
        token = create_access_token(user_id="user-456")
        payload = verify_token(token)
        assert payload["roles"] == ["user"]

    def test_custom_roles(self):
        token = create_access_token(user_id="user-789", roles=["admin"])
        payload = verify_token(token)
        assert payload["roles"] == ["admin"]

    def test_custom_expiration(self):
        token = create_access_token(
            user_id="user-abc",
            expires_delta=timedelta(minutes=5),
        )
        payload = verify_token(token)
        assert payload["sub"] == "user-abc"


class TestVerifyToken:
    """Tests for verify_token."""

    def test_valid_token(self):
        token = create_access_token(user_id="user-valid", roles=["user"])
        payload = verify_token(token)
        assert payload["sub"] == "user-valid"
        assert payload["roles"] == ["user"]
        assert "iat" in payload
        assert "exp" in payload

    def test_expired_token(self):
        token = create_access_token(
            user_id="user-expired",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(token)

    def test_invalid_token_string(self):
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token("not.a.valid.jwt")

    def test_empty_token(self):
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token("")

    def test_tampered_token(self):
        token = create_access_token(user_id="user-tamper")
        # Tamper with the token by flipping a character
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(tampered)
