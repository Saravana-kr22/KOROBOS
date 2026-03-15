"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Auth Service API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

# -- Request Schemas --


class UserSignup(BaseModel):
    """Schema for user registration."""

    email: str = Field(..., max_length=320, description="User email address")
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=300)


class DeviceInfo(BaseModel):
    """Device information for login tracking."""

    type: Optional[str] = Field(None, description="Device type: mobile, web, tablet")
    name: Optional[str] = Field(
        None, description="Device name: iPhone 15, Chrome Windows"
    )
    os: Optional[str] = Field(
        None, description="Operating system: iOS, Android, Windows"
    )
    os_version: Optional[str] = Field(None, description="OS version")
    browser: Optional[str] = Field(None, description="Browser: Chrome, Safari, Firefox")
    browser_version: Optional[str] = Field(None, description="Browser version")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Plain text password")
    device_info: Optional[DeviceInfo] = Field(
        None, description="Optional device metadata"
    )


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""

    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Request to logout."""

    refresh_token: Optional[str] = Field(
        None, description="Optional specific token to revoke"
    )


class VerifyEmailRequest(BaseModel):
    """Request to verify email."""

    token: str = Field(..., description="Email verification token")


class VerificationResendRequest(BaseModel):
    """Request to resend email verification."""

    email: str = Field(..., description="Email address")


class PasswordResetRequest(BaseModel):
    """Request password reset."""

    email: str = Field(..., description="Email address")


class PasswordResetConfirmRequest(BaseModel):
    """Confirm password reset with new password."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password"
    )


class AccountUnlockRequest(BaseModel):
    """Request account unlock via email."""

    email: str = Field(..., description="Email address")


class AccountUnlockConfirmRequest(BaseModel):
    """Confirm account unlock with token."""

    token: str = Field(..., description="Account unlock token")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: Optional[str] = Field(None, max_length=300)
    username: Optional[str] = Field(None, min_length=3, max_length=150)


# -- Response Schemas --


class UserResponse(BaseModel):
    """Public user profile response (no password)."""

    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    email_verified: bool = Field(default=False, description="Email verification status")
    email_verified_at: Optional[datetime] = Field(
        None, description="When email was verified"
    )
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response after login/signup."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPairResponse(BaseModel):
    """Full token pair response (access + refresh)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expiration
    refresh_expires_in: int  # Seconds until refresh token expiration


class AccessTokenResponse(BaseModel):
    """New access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration


class SessionResponse(BaseModel):
    """User session details."""

    id: UUID
    device_name: Optional[str]
    os: Optional[str]
    ip_address: Optional[str]
    last_activity_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class GenericResponse(BaseModel):
    """Generic response with just a message."""

    message: str
