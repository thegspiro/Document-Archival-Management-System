"""User management router — admin-only CRUD and role assignment."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    is_active: bool
    is_superadmin: bool
    roles: list[str] = []

    class Config:
        from_attributes = True


class RoleAssign(BaseModel):
    role_ids: list[int] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[UserOut])
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """List all users with pagination. Admin only."""
    from app.services import user_service

    return await user_service.list_users(db, page=page, per_page=per_page)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Create a new user account. Admin only."""
    from app.services import user_service

    user = await user_service.create_user(db, body, current_user)
    return user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Retrieve a single user by ID. Admin only."""
    from app.services import user_service

    user = await user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Update a user's profile fields. Admin only."""
    from app.services import user_service

    user = await user_service.update_user(db, user_id, body, current_user)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Soft-delete or deactivate a user. Admin only."""
    from app.services import user_service

    success = await user_service.delete_user(db, user_id, current_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/{user_id}/roles", response_model=MessageResponse)
async def assign_roles(
    user_id: int,
    body: RoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> MessageResponse:
    """Assign roles to a user, replacing any existing role assignments. Admin only."""
    from app.services import user_service

    await user_service.assign_roles(db, user_id, body.role_ids, current_user)
    return MessageResponse(detail="Roles assigned")
