"""Preservation router — format inventory, fixity reports, on-demand fixity checks,
and deaccession log. All endpoints are admin-only (prefixed /api/v1/admin).
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


@router.get("/format-inventory")
async def format_inventory(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Format distribution across the repository (PRONOM PUIDs, counts, sizes)."""
    from app.services import preservation_service

    return await preservation_service.format_inventory(db)


@router.get("/fixity-report")
async def fixity_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Summary of fixity check results — matches, mismatches, missing files."""
    from app.services import preservation_service

    return await preservation_service.fixity_report(db)


@router.post("/fixity-run", response_model=MessageResponse)
async def trigger_fixity_run(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> MessageResponse:
    """Trigger an on-demand fixity check for all files. Queues a Celery task."""
    from app.services import preservation_service

    await preservation_service.trigger_fixity_run(db, current_user)
    return MessageResponse(detail="Fixity check queued")


@router.get("/deaccession-log", response_model=PaginatedResponse[Any])
async def list_deaccession_log(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Browse the deaccession log. Entries are immutable once written."""
    from app.services import deaccession_service

    return await deaccession_service.list_log(db, page=page, per_page=per_page)
