"""Reports router — accessions, processing progress, user activity, collection summary,
and public access reports. All reports are available to archivists and above.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_role
from app.models.user import User

router = APIRouter()


@router.get("/accessions")
async def accessions_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    node_id: int | None = Query(None, description="Collection filter"),
    created_by: int | None = Query(None, description="User filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Accession report — new accessions by date range for grant reporting."""
    from app.services import report_service

    return await report_service.accessions_report(
        db, date_from=date_from, date_to=date_to,
        node_id=node_id, created_by=created_by, user=current_user,
    )


@router.get("/processing")
async def processing_report(
    node_id: int | None = Query(None, description="Collection filter"),
    as_of_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Processing progress — description completeness by collection."""
    from app.services import report_service

    return await report_service.processing_report(
        db, node_id=node_id, as_of_date=as_of_date, user=current_user,
    )


@router.get("/users")
async def users_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """User activity report — documents created/updated per user."""
    from app.services import report_service

    return await report_service.users_report(
        db, date_from=date_from, date_to=date_to,
        user_id=user_id, user=current_user,
    )


@router.get("/collection")
async def collection_report(
    node_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Collection summary — total docs, storage, OCR status, completeness distribution."""
    from app.services import report_service

    return await report_service.collection_report(
        db, node_id=node_id, user=current_user,
    )


@router.get("/public-access")
async def public_access_report(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Public access summary — published docs, exhibitions, and download counts."""
    from app.services import report_service

    return await report_service.public_access_report(
        db, date_from=date_from, date_to=date_to, user=current_user,
    )
