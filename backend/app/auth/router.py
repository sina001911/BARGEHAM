"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.database import get_session
from app.exceptions import UnauthorizedError
from app.middleware.auth import get_current_admin, get_current_user
from app.users.models import User
from app.users.schemas import (
    LoginRequest,
    Message,
    RegisterRequest,
    Token,
    TokenRefresh,
    UserReadWithRole,
)
from app.users.service import (
    authenticate_user,
    create_user,
    refresh_user_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest, session: AsyncSession = Depends(get_session)
) -> Token:
    """Authenticate user and return access + refresh tokens."""
    token = await authenticate_user(
        email=body.email,
        password=body.password,
        session=session,
    )
    if token is None:
        raise UnauthorizedError("Invalid credentials")
    return token


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, session: AsyncSession = Depends(get_session)
) -> Token:
    """Register a new user. The first registered user becomes superadmin."""
    user = await create_user(
        body,
        session,
    )
    data = {"sub": str(user.id), "email": user.email, "is_superuser": user.is_superuser}
    return Token(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


@router.post("/refresh", response_model=Token)
async def refresh(body: TokenRefresh, session: AsyncSession = Depends(get_session)) -> Token:
    """Refresh access token."""
    token = await refresh_user_token(body.refresh_token, session)
    if token is None:
        raise UnauthorizedError("Invalid refresh token")
    return token


@router.get("/me", response_model=UserReadWithRole)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Get current user profile."""
    return current_user


@router.post("/logout", response_model=Message)
async def logout() -> Message:
    """Logout (client should discard tokens)."""
    return Message(message="Logged out successfully")