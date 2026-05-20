from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.user import AdminRole


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role: AdminRole = AdminRole.OPERATOR


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    role: AdminRole | None = None
    is_active: bool | None = None


class UserPasswordChange(BaseModel):
    current_password: str | None = Field(None, min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    role: AdminRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class UserSetup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(..., min_length=8, max_length=128)


class SetupStatus(BaseModel):
    has_admin: bool
