"""User management service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_refresh_token
from app.config import settings
from app.database import get_session
from app.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.users.models import Role, User, hash_password, verify_password
from app.users.schemas import Token, UserCreate, UserReadWithRole, UserUpdate


async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    """Find a user by email."""
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(user_id: uuid.UUID, session: AsyncSession) -> User | None:
    """Find a user by ID."""
    statement = select(User).where(User.id == user_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def authenticate_user(email: str, password: str, session: AsyncSession) -> Token | None:
    """Authenticate a user and return tokens."""
    user = await get_user_by_email(email, session)
    if user is None:
        return None
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")
    if not verify_password(password, user.hashed_password):
        return None

    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()

    data = {"sub": str(user.id), "email": user.email, "is_superuser": user.is_superuser}
    return Token(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


async def refresh_user_token(refresh_token: str, session: AsyncSession) -> Token | None:
    """Refresh an access token."""
    from app.auth.jwt import verify_token

    payload = verify_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = await get_user_by_id(uuid.UUID(str(user_id)), session)
    if user is None or not user.is_active:
        return None

    data = {"sub": str(user.id), "email": user.email, "is_superuser": user.is_superuser}
    return Token(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )


async def create_user(user_data: UserCreate, session: AsyncSession) -> UserReadWithRole:
    """Create a new user."""
    existing = await get_user_by_email(user_data.email, session)
    if existing is not None:
        raise ConflictError("Email already registered")

    role = None
    if user_data.role_id is not None:
        role = await session.get(Role, user_data.role_id)
        if role is None:
            raise NotFoundError("Role not found")

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role_id=user_data.role_id,
        is_superuser=user_data.role_id is None,  # First user is superadmin
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return UserReadWithRole.model_validate(user)


async def list_users(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[UserReadWithRole]:
    """List all users."""
    statement = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await session.execute(statement)
    users = result.scalars().all()
    return [UserReadWithRole.model_validate(u) for u in users]


async def get_user(user_id: uuid.UUID, session: AsyncSession) -> UserReadWithRole:
    """Get a user by ID."""
    user = await get_user_by_id(user_id, session)
    if user is None:
        raise NotFoundError("User not found")
    return UserReadWithRole.model_validate(user)


async def update_user(
    user_id: uuid.UUID, user_data: UserUpdate, session: AsyncSession
) -> UserReadWithRole:
    """Update a user."""
    user = await get_user_by_id(user_id, session)
    if user is None:
        raise NotFoundError("User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    else:
        update_data.pop("password", None)

    for key, value in update_data.items():
        setattr(user, key, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserReadWithRole.model_validate(user)


async def delete_user(user_id: uuid.UUID, session: AsyncSession) -> None:
    """Delete a user."""
    user = await get_user_by_id(user_id, session)
    if user is None:
        raise NotFoundError("User not found")
    await session.delete(user)
    await session.commit()


async def init_default_roles(session: AsyncSession) -> None:
    """Create default roles if they don't exist."""
    defaults = [
        ("superadmin", "Super Admin", "Full access to all features"),
        ("admin", "Admin", "Administrative access"),
        ("editor", "Editor", "Can create and edit documents"),
        ("viewer", "Viewer", "Read-only access"),
        ("guest", "Guest", "Limited access"),
    ]
    for name, display, desc in defaults:
        statement = select(Role).where(Role.name == name)
        result = await session.execute(statement)
        if result.scalar_one_or_none() is None:
            session.add(Role(name=name, display_name=display, description=desc))
    await session.commit()