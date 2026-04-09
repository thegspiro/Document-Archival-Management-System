"""Persistent URL resolution — accession-number-based and ARK identifier routes.

These are public, unauthenticated routes that resolve to the document's public
page, return a tombstone, or issue a redirect.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter()


@router.get("/d/{accession_number}")
async def resolve_accession(
    accession_number: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Resolve a permanent accession-number URL.

    Returns the public document page (200), a tombstone (410 or 503), or a
    redirect depending on the document's availability_status and is_public flag.
    """
    from app.services import persistent_url_service

    return await persistent_url_service.resolve_by_accession(db, accession_number)


@router.get("/ark/{naan}/{ark_id}")
async def resolve_ark(
    naan: str,
    ark_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Resolve an ARK identifier to the document's public URL via HTTP 301 redirect."""
    from app.services import persistent_url_service

    return await persistent_url_service.resolve_by_ark(db, naan, ark_id)
