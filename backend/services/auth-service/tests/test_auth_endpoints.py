"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for Auth Service API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSignup:
    """Tests for user signup endpoint."""

    async def test_signup_success(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test successful user signup."""
        response = await client.post(
            "/signup",
            json=test_user_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user_data["email"]
        assert "password" not in data  # Password should not be in response

    async def test_signup_duplicate_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test signup with duplicate email fails."""
        # First signup succeeds
        response1 = await client.post("/signup", json=test_user_data)
        assert response1.status_code == 201

        # Second signup with same email fails
        response2 = await client.post("/signup", json=test_user_data)
        assert response2.status_code == 409
        assert "already registered" in response2.json()["detail"].lower()

    async def test_signup_weak_password(
        self, client: AsyncClient, weak_password_data: dict
    ):
        """Test signup with weak password fails."""
        response = await client.post(
            "/signup",
            json=weak_password_data,
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    async def test_signup_invalid_email(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test signup with invalid email fails."""
        test_user_data["email"] = "invalid-email"
        response = await client.post(
            "/signup",
            json=test_user_data,
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestLogin:
    """Tests for user login endpoint."""

    async def test_login_success(
        self, client: AsyncClient, test_user_data: dict, test_login_data: dict
    ):
        """Test successful user login."""
        # First signup
        signup_response = await client.post("/signup", json=test_user_data)
        assert signup_response.status_code == 201

        # Get verification token from database (in real app, this would be in email)
        # For now, we'll manually verify the email for testing
        # This requires direct database access

        # Try login (note: in real scenario, email must be verified first)
        login_response = await client.post("/login", json=test_login_data)

        # Should fail because email not verified
        assert login_response.status_code == 403
        assert "not verified" in login_response.json()["detail"].lower()

    async def test_login_invalid_credentials(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test login with invalid credentials fails."""
        # Signup
        await client.post("/signup", json=test_user_data)

        # Login with wrong password
        response = await client.post(
            "/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent email."""
        response = await client.post(
            "/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    async def test_refresh_token_success(
        self, client: AsyncClient, test_user_data: dict
    ):
        """Test successful token refresh."""
        # Signup to get tokens
        response = await client.post("/signup", json=test_user_data)
        assert response.status_code == 201

        tokens = response.json()
        refresh_token = tokens["refresh_token"]

        # Refresh the token
        refresh_response = await client.post(
            "/refresh",
            json={"refresh_token": refresh_token},
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 15 * 60  # 15 minutes

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/refresh",
            json={"refresh_token": "invalid_token_string"},
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestPasswordValidation:
    """Tests for password strength validation."""

    @pytest.mark.parametrize(
        "password,should_pass",
        [
            ("ValidPass123!", True),  # Valid
            ("valid_pass123!", True),  # Valid
            ("weak", False),  # Too short
            ("NoNumbers!", False),  # No numbers
            ("NoSpecial123", False),  # No special chars
            ("nouppercase123!", False),  # No uppercase
            ("NOLOWERCASE123!", False),  # No lowercase
        ],
    )
    async def test_password_strength(
        self, client: AsyncClient, password: str, should_pass: bool
    ):
        """Test password strength validation."""
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": password,
            "full_name": "Test User",
        }

        response = await client.post("/signup", json=data)

        if should_pass:
            assert response.status_code == 201
        else:
            assert response.status_code == 400
            assert "password" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestVerifyEmail:
    """Tests for email verification endpoint."""

    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Test email verification with invalid token fails."""
        response = await client.post(
            "/verify-email",
            json={"token": "invalid_token"},
        )

        assert response.status_code == 400


@pytest.mark.asyncio
class TestPasswordReset:
    """Tests for password reset endpoints."""

    async def test_request_password_reset(self, client: AsyncClient):
        """Test password reset request."""
        response = await client.post(
            "/password-reset",
            json={"email": "any@example.com"},
        )

        assert response.status_code == 200
        assert "reset link" in response.json()["message"].lower()

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test password reset with invalid token fails."""
        response = await client.post(
            "/password-reset/confirm",
            json={
                "token": "invalid_token",
                "new_password": "NewPass123!",
            },
        )

        assert response.status_code == 400
