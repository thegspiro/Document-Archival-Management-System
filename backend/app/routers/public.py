"""Public API router — all unauthenticated endpoints for the exhibition site.

No authentication is required. Only records with is_public=TRUE and valid
embargo dates are returned. Annotations are never exposed on these routes.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Exhibitions
# ---------------------------------------------------------------------------


@router.get("/exhibitions", response_model=list[Any])
async def list_public_exhibitions(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all published exhibitions."""
    from app.services import public_service

    return await public_service.list_exhibitions(db)


@router.get("/exhibitions/{slug}")
async def get_public_exhibition(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a published exhibition by slug, including page tree."""
    from app.services import public_service

    exhibition = await public_service.get_exhibition_by_slug(db, slug)
    if exhibition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibition not found"
        )
    return exhibition


@router.get("/exhibitions/{slug}/pages/{page_slug}")
async def get_public_exhibition_page(
    slug: str,
    page_slug: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a single exhibition page with its resolved blocks."""
    from app.services import public_service

    page = await public_service.get_exhibition_page(db, slug, page_slug)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------


@router.get("/documents/{document_id}")
async def get_public_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a public document with full metadata for display."""
    from app.services import public_service

    doc = await public_service.get_document(db, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return doc


@router.get("/documents/{document_id}/files/{file_id}")
async def serve_public_file(
    document_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Serve a public document file."""
    from app.services import public_service

    content, media_type, filename = await public_service.get_document_file(
        db, document_id, file_id
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get("/documents/{document_id}/pages", response_model=list[Any])
async def list_public_document_pages(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List public pages of a document (non-public pages show only page number)."""
    from app.services import public_service

    return await public_service.list_document_pages(db, document_id)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=PaginatedResponse[Any])
async def public_search(
    q: str | None = Query(None),
    document_type: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    creator_id: int | None = Query(None),
    language: str | None = Query(None),
    term_ids: list[int] | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Search public documents with full-text query and faceted filters."""
    from app.services import public_service

    return await public_service.search(
        db, q=q, document_type=document_type, date_from=date_from,
        date_to=date_to, creator_id=creator_id, language=language,
        term_ids=term_ids, page=page, per_page=per_page,
    )


# ---------------------------------------------------------------------------
# Authority records
# ---------------------------------------------------------------------------


@router.get("/authority/{authority_id}")
async def get_public_authority(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a public authority record with linked documents."""
    from app.services import public_service

    record = await public_service.get_authority(db, authority_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authority record not found",
        )
    return record


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


@router.get("/collections", response_model=list[Any])
async def list_public_collections(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Browse public arrangement nodes at the fonds/series level."""
    from app.services import public_service

    return await public_service.list_collections(db)


@router.get("/collections/{node_id}")
async def get_public_collection(
    node_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a public collection detail with document grid."""
    from app.services import public_service

    collection = await public_service.get_collection(db, node_id)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
    return collection


# ---------------------------------------------------------------------------
# Static narrative pages
# ---------------------------------------------------------------------------


@router.get("/pages", response_model=list[Any])
async def list_public_pages(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List published static narrative pages."""
    from app.services import public_service

    return await public_service.list_static_pages(db)


@router.get("/pages/{slug}")
async def get_public_page(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a static narrative page by slug."""
    from app.services import public_service

    page = await public_service.get_static_page(db, slug)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------


@router.get("/locations", response_model=list[Any])
async def list_public_locations(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Browse public locations."""
    from app.services import public_service

    return await public_service.list_locations(db)


@router.get("/locations/{location_id}")
async def get_public_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a public location with linked documents and events."""
    from app.services import public_service

    location = await public_service.get_location(db, location_id)
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return location


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.get("/events", response_model=list[Any])
async def list_public_events(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Browse public events."""
    from app.services import public_service

    return await public_service.list_events(db)


@router.get("/events/{event_id}")
async def get_public_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve a public event with linked documents, people, and places."""
    from app.services import public_service

    event = await public_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


# ---------------------------------------------------------------------------
# Map items (for dynamic map blocks)
# ---------------------------------------------------------------------------


@router.get("/map-items", response_model=list[Any])
async def get_map_items(
    term_ids: list[int] | None = Query(None),
    node_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return geolocated public documents for map block rendering."""
    from app.services import public_service

    return await public_service.get_map_items(
        db, term_ids=term_ids, node_id=node_id,
        date_from=date_from, date_to=date_to,
    )
