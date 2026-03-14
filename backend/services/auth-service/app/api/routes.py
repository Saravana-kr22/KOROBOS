"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Auth Service API routes — signup, login, and user profile.
"""

from uuid import UUID

from app.schemas.schema import (
    AccessTokenResponse,
    AccountUnlockConfirmRequest,
    AccountUnlockRequest,
    GenericResponse,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    SessionResponse,
    UserLogin,
    UserResponse,
    UserSignup,
    VerificationResendRequest,
    VerifyEmailRequest,
)
from app.services.service_logic import AuthService
from app.services.token_service import TokenService
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session
from backend.shared.logging.logger import get_logger

logger = get_logger("auth-service.routes")

router = APIRouter()


# -- Public Endpoints --


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def signup(
    data: UserSignup,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user account.

    Returns access_token and user profile with email_verified=false.
    User must verify email to login again after logout.
    Email verification link will be sent to the provided email address.

    Note: Initial access token is issued immediately for initial API access,
    but email must be verified before user can login again.
    """
    auth_svc = AuthService(session)
    try:
        user, _ = await auth_svc.signup(data)

        # Create token pair (user starts with unverified access token)
        token_svc = TokenService(session)
        tokens = await token_svc.create_tokens(
            user_id=user.id,
            email=user.email,
            roles=["admin"] if user.is_superuser else ["user"],
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        await session.commit()

        return {
            **tokens,
            "user": UserResponse.model_validate(user),
        }
    except ValueError as exc:
        error_msg = str(exc).lower()
        if "duplicate" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )


@router.post(
    "/login",
    tags=["Auth"],
)
async def login(
    data: UserLogin,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate an existing user and return access + refresh tokens.

    Returns TokenPairResponse with access_token and refresh_token.
    """
    auth_svc = AuthService(session)
    token_svc = TokenService(session)

    try:
        user, _ = await auth_svc.login(
            data,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Create token pair with session tracking
        tokens = await token_svc.create_tokens(
            user_id=user.id,
            email=user.email,
            roles=["admin"] if user.is_superuser else ["user"],
            device_info=data.device_info.model_dump() if data.device_info else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        await session.commit()

        return {
            **tokens,
            "user": UserResponse.model_validate(user),
        }
    except ValueError as exc:
        error_msg = str(exc).lower()
        if "locked" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(exc),
            )
        elif "not verified" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            )


# -- Token Management Endpoints --


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    tags=["Auth"],
)
async def refresh_token(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token.

    Returns new access_token.
    """
    token_svc = TokenService(session)
    try:
        tokens = await token_svc.refresh_access_token(data.refresh_token)
        await session.commit()
        return tokens
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


# -- Protected Endpoints --


@router.post(
    "/logout",
    response_model=GenericResponse,
    tags=["Auth"],
)
async def logout(
    data: LogoutRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Logout user (revoke specific or all sessions).

    If refresh_token provided in body, revokes only that session.
    Otherwise revokes all sessions for the user.
    """
    token_svc = TokenService(session)
    try:
        await token_svc.revoke_session(
            user_id=UUID(x_user_id),
            refresh_token=data.refresh_token,
        )
        await session.commit()
        return GenericResponse(message="Logged out successfully")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/logout-all",
    response_model=GenericResponse,
    tags=["Auth"],
)
async def logout_all(
    x_user_id: str = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Logout from all devices (revoke all sessions).
    """
    token_svc = TokenService(session)
    try:
        await token_svc.revoke_session(user_id=UUID(x_user_id))
        await session.commit()
        return GenericResponse(message="Logged out from all devices")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# -- Email Verification Endpoints --


@router.post(
    "/verify-email",
    response_model=UserResponse,
    tags=["Auth"],
)
async def verify_email(
    data: VerifyEmailRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify user email with verification token.
    """
    auth_svc = AuthService(session)
    try:
        user = await auth_svc.verify_email(data.token)
        await session.commit()
        return UserResponse.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/verify-email/resend",
    response_model=GenericResponse,
    tags=["Auth"],
)
async def resend_verification_email(
    data: VerificationResendRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Resend email verification link.

    Always returns success to prevent email enumeration.
    """
    auth_svc = AuthService(session)
    await auth_svc.resend_verification_email(data.email)
    await session.commit()

    return GenericResponse(
        message="If email exists and is not verified, a verification link has been sent"
    )


# -- Password Reset Endpoints --


@router.post(
    "/password-reset",
    response_model=GenericResponse,
    tags=["Auth"],
)
async def request_password_reset(
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Request password reset (sends email with reset link).

    Always returns success to prevent email enumeration.
    """
    auth_svc = AuthService(session)
    await auth_svc.request_password_reset(data.email)
    await session.commit()

    return GenericResponse(
        message="If email exists, password reset link has been sent"
    )


@router.post(
    "/password-reset/confirm",
    response_model=UserResponse,
    tags=["Auth"],
)
async def confirm_password_reset(
    data: PasswordResetConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Confirm password reset with new password.
    """
    auth_svc = AuthService(session)
    try:
        user = await auth_svc.reset_password(data.token, data.new_password)
        await session.commit()
        return UserResponse.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# -- Account Unlock Endpoints --


@router.post(
    "/account/unlock-request",
    response_model=GenericResponse,
    tags=["Auth"],
)
async def request_account_unlock(
    data: AccountUnlockRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Request account unlock (sends email with unlock link).

    Always returns success to prevent email enumeration.
    """
    auth_svc = AuthService(session)
    await auth_svc.request_account_unlock(data.email)
    await session.commit()

    return GenericResponse(
        message="If account is locked, unlock instructions have been sent to the email"
    )


@router.post(
    "/account/unlock-confirm",
    response_model=UserResponse,
    tags=["Auth"],
)
async def confirm_account_unlock(
    data: AccountUnlockConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Confirm account unlock with token from email.
    """
    auth_svc = AuthService(session)
    try:
        user = await auth_svc.confirm_account_unlock(data.token)
        await session.commit()
        return UserResponse.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/account/unlock/{user_id}",
    response_model=UserResponse,
    tags=["Admin"],
)
async def admin_unlock_account(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_user_roles: str = Header(default="", alias="X-User-Roles"),
):
    """
    Admin endpoint to unlock an account.

    Requires admin role.
    """
    # Check if caller is admin
    roles = x_user_roles.split(",") if x_user_roles else []
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    auth_svc = AuthService(session)
    try:
        user = await auth_svc.unlock_account(user_id)
        await session.commit()
        return UserResponse.model_validate(user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


# -- User Profile Endpoints --


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


@router.get(
    "/sessions",
    tags=["Auth"],
)
async def get_user_sessions(
    x_user_id: str = Header(..., alias="X-User-ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get all active sessions for the current user.

    Lists all devices currently logged in.
    """
    token_svc = TokenService(session)
    try:
        sessions = await token_svc.get_active_sessions(UUID(x_user_id))
        return {
            "sessions": [SessionResponse.model_validate(s) for s in sessions]
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/", tags=["Auth"])
async def root():
    """Auth service status."""
    return {"service": "auth-service", "status": "running"}
