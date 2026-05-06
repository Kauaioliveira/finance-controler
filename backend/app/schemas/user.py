from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.auth import CompanySummary


RoleType = Literal["admin", "analyst", "viewer"]


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: RoleType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    company: CompanySummary


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    role: RoleType
    password: str = Field(..., min_length=8)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    role: RoleType | None = None


class UpdatePasswordRequest(BaseModel):
    password: str = Field(..., min_length=8)


class UpdateUserStatusRequest(BaseModel):
    is_active: bool
