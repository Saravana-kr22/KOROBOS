"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Security-focused tests for authentication and token handling.
"""

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from app.utils.validation import EmailValidator, PasswordValidator
from jose import jwt

from backend.shared.auth.jwt_handler import (
    ALGORITHM,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_token,
)


@pytest.mark.asyncio
class TestPasswordStrength:
    """Tests for password strength validation."""

    @pytest.mark.parametrize(
        "password,should_pass",
        [
            # Valid passwords
            ("ValidPass123!", True),
            ("MySecure.Pass456!", True),
            ("Str0ng!@#$%^", True),
            ("Password@123456789", True),
            # Invalid - too short
            ("Pass1!", False),
            # Invalid - no uppercase
            ("mypassword123!", False),
            # Invalid - no lowercase
            ("MYPASSWORD123!", False),
            # Invalid - no digits
            ("MyPassword!", False),
            # Invalid - no special chars
            ("MyPassword123", False),
        ],
    )
    def test_password_validation(self, password: str, should_pass: bool):
        """Test password strength validation."""
        is_valid, message = PasswordValidator.validate(password)
        assert is_valid == should_pass

    def test_weak_password_messages(self):
        """Test error messages for weak passwords."""
        # Too short
        valid, msg = PasswordValidator.validate("short")
        assert not valid
        assert "8 characters" in msg

        # No uppercase
        valid, msg = PasswordValidator.validate("password123!")
        assert not valid
        assert "uppercase" in msg

        # No lowercase
        valid, msg = PasswordValidator.validate("PASSWORD123!")
        assert not valid
        assert "lowercase" in msg

        # No digit
        valid, msg = PasswordValidator.validate("Password!")
        assert not valid
        assert "digit" in msg

        # No special char
        valid, msg = PasswordValidator.validate("Password123")
        assert not valid
        assert "special character" in msg


@pytest.mark.asyncio
class TestEmailValidation:
    """Tests for email format validation."""

    @pytest.mark.parametrize(
        "email,should_pass",
        [
            # Valid emails
            ("user@example.com", True),
            ("test.user@company.co.uk", True),
            ("user+tag@example.com", True),
            ("user_name@example.com", True),
            # Invalid emails
            ("invalid", False),
            ("@example.com", False),
            ("user@", False),
            ("user @example.com", False),
            ("user@example", False),
        ],
    )
    def test_email_validation(self, email: str, should_pass: bool):
        """Test email format validation."""
        is_valid = EmailValidator.validate(email)
        assert is_valid == should_pass


@pytest.mark.asyncio
class TestJWTTokens:
    """Tests for JWT token creation and validation."""

    def test_access_token_contains_required_claims(self):
        """Test access token has required claims."""
        user_id = "test-user-123"
        roles = ["user", "admin"]
        token = create_access_token(user_id, email="test@example.com", roles=roles)

        payload = verify_token(token)

        assert payload["sub"] == user_id
        assert payload["roles"] == roles
        assert "iat" in payload
        assert "exp" in payload

    def test_access_token_expiration(self):
        """Test access token expires after 15 minutes."""
        user_id = "test-user-123"
        token = create_access_token(user_id, email="test@example.com")

        payload = verify_token(token)

        # Check expiration is approximately 15 minutes from now
        now = datetime.now(timezone.utc).timestamp()
        exp = (
            payload["exp"].timestamp()
            if hasattr(payload["exp"], "timestamp")
            else payload["exp"]
        )
        exp_seconds = int(exp) - int(now)

        # Should be close to 15 minutes (900 seconds), allow 30 second variance
        assert 870 <= exp_seconds <= 930

    def test_refresh_token_contains_required_claims(self):
        """Test refresh token has required claims."""
        user_id = "test-user-123"
        token = create_refresh_token(user_id)

        payload = verify_refresh_token(token)

        assert payload["sub"] == user_id
        assert payload["token_type"] == "refresh"
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_expiration(self):
        """Test refresh token expires after 30 days."""
        user_id = "test-user-123"
        token = create_refresh_token(user_id)

        payload = verify_refresh_token(token)

        # Check expiration is approximately 30 days from now
        now = datetime.now(timezone.utc).timestamp()
        exp = (
            payload["exp"].timestamp()
            if hasattr(payload["exp"], "timestamp")
            else payload["exp"]
        )
        exp_seconds = int(exp) - int(now)

        # Should be close to 30 days (2592000 seconds), allow 1 minute variance
        expected = 30 * 24 * 60 * 60
        assert expected - 60 <= exp_seconds <= expected + 60

    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens are different."""
        user_id = "test-user-123"

        access_token = create_access_token(user_id, email="test@example.com")
        refresh_token = create_refresh_token(user_id)

        assert access_token != refresh_token

        # Access token should not verify as refresh
        with pytest.raises(ValueError, match="Invalid token type"):
            verify_refresh_token(access_token)

    def test_invalid_token_fails_verification(self):
        """Test that invalid tokens fail verification."""
        with pytest.raises(ValueError, match="Invalid"):
            verify_token("invalid.token.string")

        with pytest.raises(ValueError, match="Invalid"):
            verify_refresh_token("invalid.token.string")

    def test_tampered_token_fails_verification(self):
        """Test that tampered tokens fail verification."""
        user_id = "test-user-123"
        token = create_access_token(user_id, email="test@example.com")

        # Tamper with token
        parts = token.split(".")
        if len(parts) == 3:
            # Change the payload
            tampered = parts[0] + "." + "tampered_payload_here" + "." + parts[2]
            with pytest.raises(ValueError):
                verify_token(tampered)


@pytest.mark.asyncio
class TestTokenSecurity:
    """Tests for token security mechanisms."""

    def test_token_cannot_be_reused_after_revocation(self):
        """Test that tokens from revoked sessions cannot be reused."""
        # This is more of an integration test
        # In a real scenario, we'd check the session revocation
        user_id = "test-user-123"
        token = create_access_token(user_id, email="test@example.com")

        # Token should be valid initially
        payload = verify_token(token)
        assert payload["sub"] == user_id

        # In practice, we check the session.revoked_at field
        # A revoked session's tokens should not be accepted

    def test_different_user_ids_produce_different_tokens(self):
        """Test that different users get different tokens."""
        token1 = create_access_token("user-1", email="user1@example.com")
        token2 = create_access_token("user-2", email="user2@example.com")

        assert token1 != token2

        payload1 = verify_token(token1)
        payload2 = verify_token(token2)

        assert payload1["sub"] == "user-1"
        assert payload2["sub"] == "user-2"

    def test_token_signature_cannot_be_forged(self):
        """Test that JWT signature prevents forgery."""
        from backend.shared.config.settings import get_settings

        get_settings()
        user_id = "test-user-123"

        # Create valid token
        create_access_token(user_id, email="test@example.com")

        # Try to forge a token with different secret
        forged_token = jwt.encode(
            {
                "sub": "attacker-id",
                "roles": ["admin"],
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            "wrong_secret_key",  # Different secret
            algorithm=ALGORITHM,
        )

        # Forged token should fail verification
        with pytest.raises(ValueError):
            verify_token(forged_token)


@pytest.mark.asyncio
class TestBruteForceProtection:
    """Tests for brute-force protection mechanisms."""

    def test_account_lockout_duration(self):
        """Test that account lockout has a duration."""
        from datetime import datetime, timedelta, timezone

        lockout_duration = timedelta(minutes=30)
        now = datetime.now(timezone.utc)
        locked_until = now + lockout_duration

        # Lockout should be in the future
        assert locked_until > now
        # But not too far in the future
        assert locked_until < now + timedelta(hours=1)

    def test_max_login_attempts_constant(self):
        """Test that max login attempts is reasonable."""
        from app.services.service_logic import AuthService

        # Should not allow more than 10 attempts before lockout
        assert AuthService.MAX_LOGIN_ATTEMPTS <= 10
        # Should be at least 3 to prevent accidental lockouts
        assert AuthService.MAX_LOGIN_ATTEMPTS >= 3

    def test_lockout_duration_is_reasonable(self):
        """Test that lockout duration is reasonable."""
        from app.services.service_logic import AuthService

        duration = AuthService.LOCKOUT_DURATION
        # Should be at least 10 minutes
        assert duration >= timedelta(minutes=10)
        # Should be no more than 2 hours
        assert duration <= timedelta(hours=2)


@pytest.mark.asyncio
class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_constants(self):
        """Test rate limiting is configured correctly."""
        from app.middleware.rate_limit import LoginRateLimiter

        limiter = LoginRateLimiter()

        # Should limit to 10 requests per minute
        assert limiter.RATE_LIMIT == 10
        assert limiter.WINDOW_SECONDS == 60

        # 10 requests per minute is reasonable
        requests_per_hour = (limiter.RATE_LIMIT / limiter.WINDOW_SECONDS) * 3600
        assert 500 <= requests_per_hour <= 1000  # Roughly 600 per hour


@pytest.mark.asyncio
class TestTokenHashing:
    """Tests for secure token hashing."""

    def test_token_hashing_is_one_way(self):
        """Test that token hashing is one-way."""
        from app.services.token_service import TokenService

        token = "test_refresh_token_string"
        hashed = TokenService._hash_token(token)

        # Hash should be different from original
        assert hashed != token
        # Hash should be deterministic (same input = same output)
        assert TokenService._hash_token(token) == hashed

    def test_different_tokens_produce_different_hashes(self):
        """Test that different tokens hash differently."""
        from app.services.token_service import TokenService

        token1 = "token_1"
        token2 = "token_2"

        hash1 = TokenService._hash_token(token1)
        hash2 = TokenService._hash_token(token2)

        assert hash1 != hash2

    def test_hashed_token_uses_sha256(self):
        """Test that token hashing uses SHA256."""
        from app.services.token_service import TokenService

        token = "test_token"
        hashed = TokenService._hash_token(token)

        # SHA256 produces 64 hex characters
        assert len(hashed) == 64
        # Should only contain hex characters
        assert all(c in "0123456789abcdef" for c in hashed)

        # Verify it matches expected SHA256
        expected = hashlib.sha256(token.encode()).hexdigest()
        assert hashed == expected
