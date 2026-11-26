"""User and role models."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from passlib.hash import argon2
from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RoleBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=50)
    display_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)


class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    full_name: str = Field(max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id")


class UserUpdate(SQLModel):
    full_name: str | None = None
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role_id: uuid.UUID | None = None


class UserRead(UserBase):
    id: uuid.UUID
    role_id: uuid.UUID | None = None
    created_at: datetime
    last_login: datetime | None = None


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(max_length=255)
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id")
    created_at: datetime = Field(default_factory=_utcnow)
    last_login: datetime | None = Field(default=None)

    role: Optional[Role] = Relationship()


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return argon2.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return argon2.verify(password, hashed)