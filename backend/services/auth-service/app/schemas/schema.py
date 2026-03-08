"""
CortexOS — Second Brain Operating System

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


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Plain text password")


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
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response after login/signup."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
