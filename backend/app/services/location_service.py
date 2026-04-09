"""Location service — CRUD for controlled place records and linked entities."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_location_link import DocumentLocationLink
from app.models.event_location_link import EventLocationLink
from app.models.location import Location
from app.services.audit_service import AuditService


class LocationService:
    """Business logic for location entities — the place authority file."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        data: dict[str, Any],
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> Location:
        """Create a new location record."""
        data.setdefault("created_by", created_by)
        location = Location(**data)
        db.add(location)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="location.create",
            resource_type="location",
            resource_id=location.id,
            detail={"authorized_name": location.authorized_name},
            ip_address=ip_address,
        )
        return location

    @staticmethod
    async def get(db: AsyncSession, *, location_id: int) -> Location:
        """Return a location by ID, or raise 404."""
        result = await db.execute(select(Location).where(Location.id == location_id))
        location = result.scalar_one_or_none()
        if location is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found",
            )
        return location

    @staticmethod
    async def list_locations(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        q: str | None = None,
    ) -> dict:
        """Return a paginated list of locations, optionally filtered by name."""
        query = select(Location)
        if q:
            query = query.where(Location.authorized_name.ilike(f"%{q}%"))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Location.authorized_name).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        location_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Location:
        """Update mutable fields on a location record."""
        location = await LocationService.get(db, location_id=location_id)

        protected = {"id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(location, key):
                setattr(location, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="location.update",
            resource_type="location",
            resource_id=location.id,
            detail=changes,
            ip_address=ip_address,
        )
        return location

    @staticmethod
    async def delete(
        db: AsyncSession,
        *,
        location_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete a location record."""
        location = await LocationService.get(db, location_id=location_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="location.delete",
            resource_type="location",
            resource_id=location.id,
            detail={"authorized_name": location.authorized_name},
            ip_address=ip_address,
        )
        await db.delete(location)
        await db.flush()

    # ------------------------------------------------------------------
    # Linked documents
    # ------------------------------------------------------------------

    @staticmethod
    async def get_linked_documents(
        db: AsyncSession,
        *,
        location_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return paginated document-location links for this location."""
        query = select(DocumentLocationLink).where(
            DocumentLocationLink.location_id == location_id
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(DocumentLocationLink.id).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    # ------------------------------------------------------------------
    # Linked events
    # ------------------------------------------------------------------

    @staticmethod
    async def get_linked_events(
        db: AsyncSession,
        *,
        location_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return paginated event-location links for this location."""
        query = select(EventLocationLink).where(
            EventLocationLink.location_id == location_id
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(EventLocationLink.id).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}
