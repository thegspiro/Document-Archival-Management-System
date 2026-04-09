"""User and role management schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for POST /api/v1/users — admin creates a new user."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Plaintext password")
    display_name: str = Field(min_length=1, max_length=255)
    is_active: bool = True
    is_superadmin: bool = False
    role_ids: list[int] = Field(
        default_factory=list,
        description="Role IDs to assign immediately on creation",
    )


class UserUpdate(BaseModel):
    """Schema for PATCH /api/v1/users/{id}. All fields optional."""

    email: EmailStr | None = None
    password: str | None = Field(
        default=None, min_length=8, max_length=128, description="New plaintext password"
    )
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None
    is_superadmin: bool | None = None


class RoleResponse(BaseModel):
    """Response schema for a single role."""

    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """Full user representation for admin endpoints."""

    id: int
    email: str
    display_name: str
    is_active: bool
    is_superadmin: bool
    last_login_at: datetime | None = None
    roles: list[RoleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleAssignRequest(BaseModel):
    """Schema for POST /api/v1/users/{id}/roles — assign roles to a user."""

    role_ids: list[int] = Field(min_length=1, description="Role IDs to assign")
