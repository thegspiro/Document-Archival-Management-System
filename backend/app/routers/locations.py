"""Locations router — CRUD for controlled place entities plus linked documents and events."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class LocationCreate(BaseModel):
    authorized_name: str = Field(min_length=1, max_length=500)
    variant_names: str | None = None
    location_type_id: int | None = None
    geo_latitude: float | None = None
    geo_longitude: float | None = None
    address: str | None = None
    description: str | None = None
    date_established: str | None = None
    date_ceased: str | None = None
    parent_location_id: int | None = None
    wikidata_qid: str | None = None
    is_public: bool = False
    public_description: str | None = None


class LocationUpdate(BaseModel):
    authorized_name: str | None = None
    variant_names: str | None = None
    location_type_id: int | None = None
    geo_latitude: float | None = None
    geo_longitude: float | None = None
    address: str | None = None
    description: str | None = None
    date_established: str | None = None
    date_ceased: str | None = None
    parent_location_id: int | None = None
    wikidata_qid: str | None = None
    is_public: bool | None = None
    public_description: str | None = None


class LocationOut(BaseModel):
    id: int
    authorized_name: str
    variant_names: str | None = None
    location_type_id: int | None = None
    geo_latitude: float | None = None
    geo_longitude: float | None = None
    address: str | None = None
    description: str | None = None
    is_public: bool = False
    parent_location_id: int | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[LocationOut])
async def list_locations(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, description="Name search"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List locations with pagination and optional search."""
    from app.services import location_service

    return await location_service.list_locations(
        db, page=page, per_page=per_page, q=q,
    )


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a new location entity."""
    from app.services import location_service

    return await location_service.create_location(db, body, current_user)


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single location by ID."""
    from app.services import location_service

    loc = await location_service.get_location(db, location_id)
    if loc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return loc


@router.patch("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: int,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update a location entity."""
    from app.services import location_service

    loc = await location_service.update_location(db, location_id, body, current_user)
    if loc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )
    return loc


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete a location entity."""
    from app.services import location_service

    success = await location_service.delete_location(db, location_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
        )


# ---------------------------------------------------------------------------
# Linked entities
# ---------------------------------------------------------------------------


@router.get("/{location_id}/documents", response_model=PaginatedResponse[Any])
async def list_location_documents(
    location_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all documents linked to this location."""
    from app.services import location_service

    return await location_service.list_documents(
        db, location_id, page=page, per_page=per_page,
    )


@router.get("/{location_id}/events", response_model=list[Any])
async def list_location_events(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all events at this location."""
    from app.services import location_service

    return await location_service.list_events(db, location_id)
