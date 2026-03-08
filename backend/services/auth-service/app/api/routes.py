"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Auth Service API routes — signup, login, and user profile.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schema import (
    UserSignup,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.services.service_logic import AuthService

from backend.shared.database.connection import get_db_session
from backend.shared.logging.logger import get_logger

logger = get_logger("auth-service.routes")

router = APIRouter()


# -- Public Endpoints --


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def signup(
    data: UserSignup,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.

    Returns a JWT access token and user profile.
    """
    svc = AuthService(session)
    try:
        user, token = await svc.signup(data)
        await session.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    tags=["Auth"],
)
async def login(
    data: UserLogin,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate an existing user and return a JWT.
    """
    svc = AuthService(session)
    try:
        user, token = await svc.login(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


# -- Protected Endpoints --


@router.get(
    "/me",
    response_model=UserResponse,
    tags=["Auth"],
)
async def get_current_user(
    x_user_id: str = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get the current authenticated user's profile.

    X-User-ID header is injected by the API Gateway after JWT validation.
    """
    svc = AuthService(session)
    user = await svc.get_user(UUID(x_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/", tags=["Auth"])
async def root():
    """Auth service status."""
    return {"service": "auth-service", "status": "running"}
