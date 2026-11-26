"""User management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_admin, get_current_user
from app.database import get_session
from app.users.models import User
from app.users.schemas import Message, UserReadWithRole, UserUpdate
from app.users.service import delete_user, get_user, list_users, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserReadWithRole])
async def list_users_endpoint(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> list[UserReadWithRole]:
    """List all users (admin only)."""
    return await list_users(session, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserReadWithRole)
async def get_user_endpoint(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserReadWithRole:
    """Get a user by ID."""
    return await get_user(user_id, session)


@router.patch("/{user_id}", response_model=UserReadWithRole)
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserReadWithRole:
    """Update a user."""
    return await update_user(user_id, user_data, session)


@router.delete("/{user_id}", response_model=Message)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Message:
    """Delete a user."""
    await delete_user(user_id, session)
    return Message(message="User deleted successfully")