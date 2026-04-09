"""Authentication request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials submitted to POST /api/v1/auth/login."""

    email: EmailStr
    password: str = Field(min_length=1, description="User password")


class TokenResponse(BaseModel):
    """Returned by login and refresh endpoints.

    The actual JWT tokens are delivered as httpOnly cookies (§7.1), so this body
    carries only non-sensitive confirmation fields.
    """

    access_token_expires_at: datetime = Field(
        description="UTC expiry time of the access token cookie"
    )
    token_type: str = Field(default="bearer")


class UserResponse(BaseModel):
    """Lightweight user representation returned alongside auth responses."""

    id: int
    email: str
    display_name: str
    is_active: bool
    is_superadmin: bool
    roles: list[str] = Field(
        default_factory=list,
        description="Role names currently held by this user",
    )
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
