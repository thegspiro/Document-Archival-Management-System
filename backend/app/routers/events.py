"""Events router — CRUD for historical events plus linked documents, authorities, and locations."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    event_type_id: int
    date_display: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    primary_location_id: int | None = None
    description: str | None = None
    is_public: bool = False
    public_description: str | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    event_type_id: int | None = None
    date_display: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    primary_location_id: int | None = None
    description: str | None = None
    is_public: bool | None = None
    public_description: str | None = None


class EventOut(BaseModel):
    id: int
    title: str
    event_type_id: int
    date_display: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    primary_location_id: int | None = None
    is_public: bool = False

    class Config:
        from_attributes = True


class EventDocumentLinkCreate(BaseModel):
    document_id: int
    link_type: str = "about"
    notes: str | None = None


class EventDocumentLinkOut(BaseModel):
    id: int
    event_id: int
    document_id: int
    link_type: str
    notes: str | None = None

    class Config:
        from_attributes = True


class EventAuthorityLinkCreate(BaseModel):
    authority_id: int
    role_id: int
    notes: str | None = None


class EventAuthorityLinkOut(BaseModel):
    id: int
    event_id: int
    authority_id: int
    role_id: int
    notes: str | None = None

    class Config:
        from_attributes = True


class EventLocationLinkCreate(BaseModel):
    location_id: int
    link_type: str = "primary"
    notes: str | None = None


class EventLocationLinkOut(BaseModel):
    id: int
    event_id: int
    location_id: int
    link_type: str
    notes: str | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[EventOut])
async def list_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, description="Title search"),
    event_type_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List events with pagination and optional filters."""
    from app.services import event_service

    return await event_service.list_events(
        db, page=page, per_page=per_page, q=q, event_type_id=event_type_id,
    )


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a new event."""
    from app.services import event_service

    return await event_service.create_event(db, body, current_user)


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single event by ID."""
    from app.services import event_service

    event = await event_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.patch("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update an event."""
    from app.services import event_service

    event = await event_service.update_event(db, event_id, body, current_user)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete an event."""
    from app.services import event_service

    success = await event_service.delete_event(db, event_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )


# ---------------------------------------------------------------------------
# Document links
# ---------------------------------------------------------------------------


@router.get("/{event_id}/documents", response_model=list[EventDocumentLinkOut])
async def list_event_documents(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List documents linked to this event."""
    from app.services import event_service

    return await event_service.list_document_links(db, event_id)


@router.post(
    "/{event_id}/documents",
    response_model=EventDocumentLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_document_link(
    event_id: int,
    body: EventDocumentLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Link a document to an event."""
    from app.services import event_service

    return await event_service.create_document_link(db, event_id, body, current_user)


@router.delete(
    "/{event_id}/documents/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event_document_link(
    event_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove a document link from an event."""
    from app.services import event_service

    success = await event_service.delete_document_link(db, event_id, link_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )


# ---------------------------------------------------------------------------
# Authority links
# ---------------------------------------------------------------------------


@router.get("/{event_id}/authorities", response_model=list[EventAuthorityLinkOut])
async def list_event_authorities(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List authority records linked to this event."""
    from app.services import event_service

    return await event_service.list_authority_links(db, event_id)


@router.post(
    "/{event_id}/authorities",
    response_model=EventAuthorityLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_authority_link(
    event_id: int,
    body: EventAuthorityLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Link an authority record to an event with a role."""
    from app.services import event_service

    return await event_service.create_authority_link(db, event_id, body, current_user)


@router.delete(
    "/{event_id}/authorities/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event_authority_link(
    event_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove an authority link from an event."""
    from app.services import event_service

    success = await event_service.delete_authority_link(
        db, event_id, link_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )


# ---------------------------------------------------------------------------
# Location links
# ---------------------------------------------------------------------------


@router.get("/{event_id}/locations", response_model=list[EventLocationLinkOut])
async def list_event_locations(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List locations linked to this event."""
    from app.services import event_service

    return await event_service.list_location_links(db, event_id)


@router.post(
    "/{event_id}/locations",
    response_model=EventLocationLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_event_location_link(
    event_id: int,
    body: EventLocationLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Link a location to an event."""
    from app.services import event_service

    return await event_service.create_location_link(db, event_id, body, current_user)


@router.delete(
    "/{event_id}/locations/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event_location_link(
    event_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove a location link from an event."""
    from app.services import event_service

    success = await event_service.delete_location_link(
        db, event_id, link_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )
