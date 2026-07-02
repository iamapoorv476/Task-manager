"""Pydantic schemas for the User resource.

Deliberately separate from the SQLAlchemy `User` model: the ORM model
describes what's persisted, these describe what crosses the HTTP
boundary. Notably, `UserCreate` has no `role` field -- role is never
client-settable at registration time. Allowing it would let anyone
register as an ADMIN by simply including that field in the request body.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "password": "SecurePass123",
            }
        }
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("name must be at least 2 characters long")
        return v

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            # bcrypt hard-caps input at 72 bytes; reject cleanly here
            # (422) rather than letting it fail deep inside hash_password.
            raise ValueError("password must be at most 72 bytes long")
        if not any(c.isdigit() for c in v):
            raise ValueError("password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("password must contain at least one letter")
        return v


class UserRead(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "role": "USER",
                "created_at": "2026-06-01T09:15:00Z",
                "updated_at": "2026-06-01T09:15:00Z",
            }
        },
    )

    id: uuid.UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime