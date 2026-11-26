"""User and role schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class RoleRead(SQLModel):
    id: uuid.UUID
    name: str
    display_name: str
    description: str | None = None


class UserRead(SQLModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role_id: uuid.UUID | None = None
    created_at: datetime
    last_login: datetime | None = None


class UserReadWithRole(UserRead):
    role: RoleRead | None = None


class UserCreate(SQLModel):
    email: str
    full_name: str
    password: str
    role_id: uuid.UUID | None = None


class LoginRequest(SQLModel):
    email: str
    password: str


class RegisterRequest(SQLModel):
    email: str
    full_name: str
    password: str
    role_id: uuid.UUID | None = None


class UserUpdate(SQLModel):
    full_name: str | None = None
    email: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    password: str | None = None
    role_id: uuid.UUID | None = None


class Token(SQLModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(SQLModel):
    refresh_token: str


class Message(SQLModel):
    message: str