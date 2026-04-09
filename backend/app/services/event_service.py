"""Event service — CRUD for historical events and their entity links."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.event_authority_link import EventAuthorityLink
from app.models.event_document_link import EventDocumentLink
from app.models.event_location_link import EventLocationLink
from app.services.audit_service import AuditService


class EventService:
    """Business logic for named historical events and their links to
    documents, authority records, and locations."""

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
    ) -> Event:
        """Create a new event record."""
        data.setdefault("created_by", created_by)
        event = Event(**data)
        db.add(event)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="event.create",
            resource_type="event",
            resource_id=event.id,
            detail={"title": event.title},
            ip_address=ip_address,
        )
        return event

    @staticmethod
    async def get(db: AsyncSession, *, event_id: int) -> Event:
        """Return an event by ID, or raise 404."""
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event

    @staticmethod
    async def list_events(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        q: str | None = None,
    ) -> dict:
        """Return a paginated, optionally filtered list of events."""
        query = select(Event)
        if q:
            query = query.where(Event.title.ilike(f"%{q}%"))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Event.date_start.desc().nullslast(), Event.id.desc())
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        event_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Event:
        """Update mutable fields on an event."""
        event = await EventService.get(db, event_id=event_id)

        protected = {"id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(event, key):
                setattr(event, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="event.update",
            resource_type="event",
            resource_id=event.id,
            detail=changes,
            ip_address=ip_address,
        )
        return event

    @staticmethod
    async def delete(
        db: AsyncSession,
        *,
        event_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an event record."""
        event = await EventService.get(db, event_id=event_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="event.delete",
            resource_type="event",
            resource_id=event.id,
            detail={"title": event.title},
            ip_address=ip_address,
        )
        await db.delete(event)
        await db.flush()

    # ------------------------------------------------------------------
    # Document links
    # ------------------------------------------------------------------

    @staticmethod
    async def add_document_link(
        db: AsyncSession,
        *,
        event_id: int,
        document_id: int,
        link_type: str = "about",
        notes: str | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> EventDocumentLink:
        """Link a document to an event."""
        link = EventDocumentLink(
            event_id=event_id,
            document_id=document_id,
            link_type=link_type,
            notes=notes,
            created_by=created_by,
        )
        db.add(link)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="event_document_link.create",
            resource_type="event_document_link",
            resource_id=link.id,
            detail={"event_id": event_id, "document_id": document_id, "link_type": link_type},
            ip_address=ip_address,
        )
        return link

    @staticmethod
    async def get_document_links(
        db: AsyncSession, *, event_id: int
    ) -> list[EventDocumentLink]:
        """Return all document links for an event."""
        result = await db.execute(
            select(EventDocumentLink).where(EventDocumentLink.event_id == event_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_document_link(
        db: AsyncSession,
        *,
        link_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Remove a document link from an event."""
        result = await db.execute(
            select(EventDocumentLink).where(EventDocumentLink.id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event-document link not found",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="event_document_link.delete",
            resource_type="event_document_link",
            resource_id=link.id,
            detail={"event_id": link.event_id, "document_id": link.document_id},
            ip_address=ip_address,
        )
        await db.delete(link)
        await db.flush()

    # ------------------------------------------------------------------
    # Authority links
    # ------------------------------------------------------------------

    @staticmethod
    async def add_authority_link(
        db: AsyncSession,
        *,
        event_id: int,
        authority_id: int,
        role_id: int,
        notes: str | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> EventAuthorityLink:
        """Link an authority record to an event with a specified role."""
        link = EventAuthorityLink(
            event_id=event_id,
            authority_id=authority_id,
            role_id=role_id,
            notes=notes,
            created_by=created_by,
        )
        db.add(link)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="event_authority_link.create",
            resource_type="event_authority_link",
            resource_id=link.id,
            detail={"event_id": event_id, "authority_id": authority_id, "role_id": role_id},
            ip_address=ip_address,
        )
        return link

    @staticmethod
    async def get_authority_links(
        db: AsyncSession, *, event_id: int
    ) -> list[EventAuthorityLink]:
        """Return all authority links for an event."""
        result = await db.execute(
            select(EventAuthorityLink).where(EventAuthorityLink.event_id == event_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_authority_link(
        db: AsyncSession,
        *,
        link_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Remove an authority link from an event."""
        result = await db.execute(
            select(EventAuthorityLink).where(EventAuthorityLink.id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event-authority link not found",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="event_authority_link.delete",
            resource_type="event_authority_link",
            resource_id=link.id,
            detail={"event_id": link.event_id, "authority_id": link.authority_id},
            ip_address=ip_address,
        )
        await db.delete(link)
        await db.flush()

    # ------------------------------------------------------------------
    # Location links
    # ------------------------------------------------------------------

    @staticmethod
    async def add_location_link(
        db: AsyncSession,
        *,
        event_id: int,
        location_id: int,
        link_type: str = "primary",
        notes: str | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> EventLocationLink:
        """Link a location to an event."""
        link = EventLocationLink(
            event_id=event_id,
            location_id=location_id,
            link_type=link_type,
            notes=notes,
            created_by=created_by,
        )
        db.add(link)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="event_location_link.create",
            resource_type="event_location_link",
            resource_id=link.id,
            detail={"event_id": event_id, "location_id": location_id, "link_type": link_type},
            ip_address=ip_address,
        )
        return link

    @staticmethod
    async def get_location_links(
        db: AsyncSession, *, event_id: int
    ) -> list[EventLocationLink]:
        """Return all location links for an event."""
        result = await db.execute(
            select(EventLocationLink).where(EventLocationLink.event_id == event_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_location_link(
        db: AsyncSession,
        *,
        link_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Remove a location link from an event."""
        result = await db.execute(
            select(EventLocationLink).where(EventLocationLink.id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event-location link not found",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="event_location_link.delete",
            resource_type="event_location_link",
            resource_id=link.id,
            detail={"event_id": link.event_id, "location_id": link.location_id},
            ip_address=ip_address,
        )
        await db.delete(link)
        await db.flush()
