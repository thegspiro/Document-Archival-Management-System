"""System settings router — admin-only GET and PATCH for key-value settings."""

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_role
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class SettingsOut(BaseModel):
    """All system settings as a flat key-value map."""

    settings: dict[str, Any]


class SettingsUpdate(BaseModel):
    """Partial update — only provided keys are written."""

    settings: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=SettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Retrieve all system settings. Admin only."""
    from app.services import settings_service

    values = await settings_service.get_all(db)
    return SettingsOut(settings=values)


@router.patch("", response_model=SettingsOut)
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Update one or more system settings. Admin only."""
    from app.services import settings_service

    values = await settings_service.update(db, body.settings, current_user)
    return SettingsOut(settings=values)
