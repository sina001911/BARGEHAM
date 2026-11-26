"""Authentication dependencies — JWT verification and RBAC."""
from __future__ import annotations

import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import verify_token
from app.database import get_session
from app.exceptions import UnauthorizedError
from app.users.models import User
from app.users.service import get_user_by_id


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Dependency that returns the current authenticated user."""
    auth_header = request.headers.get("Authorization", "")
    token: str | None = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if token is None:
        raise UnauthorizedError("Not authenticated")

    payload = verify_token(token)
    if payload is None:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token")

    user = await get_user_by_id(uuid.UUID(str(user_id)), session)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin privileges."""
    if not current_user.is_superuser:
        raise UnauthorizedError("Not enough permissions")
    return current_user