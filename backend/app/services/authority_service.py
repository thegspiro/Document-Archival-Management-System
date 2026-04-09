"""Authority record service — CRUD, document links, relationships, and Wikidata."""

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.authority_record import AuthorityRecord
from app.models.authority_relationship import AuthorityRelationship
from app.models.document import Document
from app.models.document_authority_link import DocumentAuthorityLink
from app.services.audit_service import AuditService

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"


class AuthorityService:
    """Business logic for authority records (persons, organizations, families)."""

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
    ) -> AuthorityRecord:
        """Create a new authority record."""
        data.setdefault("created_by", created_by)
        record = AuthorityRecord(**data)
        db.add(record)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="authority_record.create",
            resource_type="authority_record",
            resource_id=record.id,
            detail={"authorized_name": record.authorized_name, "entity_type": record.entity_type},
            ip_address=ip_address,
        )
        return record

    @staticmethod
    async def get(db: AsyncSession, *, record_id: int) -> AuthorityRecord:
        """Return a single authority record by ID, or raise 404."""
        result = await db.execute(
            select(AuthorityRecord).where(AuthorityRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authority record not found",
            )
        return record

    @staticmethod
    async def list_records(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        entity_type: str | None = None,
        q: str | None = None,
    ) -> dict:
        """Return a paginated, optionally filtered list of authority records."""
        query = select(AuthorityRecord)
        if entity_type:
            query = query.where(AuthorityRecord.entity_type == entity_type)
        if q:
            query = query.where(AuthorityRecord.authorized_name.ilike(f"%{q}%"))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(AuthorityRecord.authorized_name).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def update(
        db: AsyncSession,
        *,
        record_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> AuthorityRecord:
        """Update mutable fields on an authority record."""
        record = await AuthorityService.get(db, record_id=record_id)

        protected = {"id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(record, key):
                setattr(record, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="authority_record.update",
            resource_type="authority_record",
            resource_id=record.id,
            detail=changes,
            ip_address=ip_address,
        )
        return record

    @staticmethod
    async def delete(
        db: AsyncSession,
        *,
        record_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an authority record."""
        record = await AuthorityService.get(db, record_id=record_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="authority_record.delete",
            resource_type="authority_record",
            resource_id=record.id,
            detail={"authorized_name": record.authorized_name},
            ip_address=ip_address,
        )
        await db.delete(record)
        await db.flush()

    # ------------------------------------------------------------------
    # Document queries
    # ------------------------------------------------------------------

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        *,
        record_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return documents where this authority is the ISAD(G) creator."""
        query = select(Document).where(Document.creator_id == record_id)
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(query.order_by(Document.id).offset(offset).limit(per_page))
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def get_document_links(
        db: AsyncSession,
        *,
        record_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return all document links (any role) for this authority record."""
        query = select(DocumentAuthorityLink).where(
            DocumentAuthorityLink.authority_id == record_id
        )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(query.order_by(DocumentAuthorityLink.id).offset(offset).limit(per_page))
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    # ------------------------------------------------------------------
    # Authority-to-authority relationships
    # ------------------------------------------------------------------

    @staticmethod
    async def add_relationship(
        db: AsyncSession,
        *,
        source_id: int,
        target_id: int,
        relationship_type_id: int,
        date_start: Any = None,
        date_end: Any = None,
        notes: str | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> AuthorityRelationship:
        """Create a directional relationship between two authority records."""
        rel = AuthorityRelationship(
            source_authority_id=source_id,
            target_authority_id=target_id,
            relationship_type_id=relationship_type_id,
            date_start=date_start,
            date_end=date_end,
            notes=notes,
            created_by=created_by,
        )
        db.add(rel)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="authority_relationship.create",
            resource_type="authority_relationship",
            resource_id=rel.id,
            detail={"source": source_id, "target": target_id},
            ip_address=ip_address,
        )
        return rel

    @staticmethod
    async def get_relationships(
        db: AsyncSession,
        *,
        record_id: int,
    ) -> list[AuthorityRelationship]:
        """Return all relationships where this record is source or target."""
        result = await db.execute(
            select(AuthorityRelationship).where(
                (AuthorityRelationship.source_authority_id == record_id)
                | (AuthorityRelationship.target_authority_id == record_id)
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_relationship(
        db: AsyncSession,
        *,
        relationship_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an authority relationship."""
        result = await db.execute(
            select(AuthorityRelationship).where(AuthorityRelationship.id == relationship_id)
        )
        rel = result.scalar_one_or_none()
        if rel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authority relationship not found",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="authority_relationship.delete",
            resource_type="authority_relationship",
            resource_id=rel.id,
            detail={
                "source": rel.source_authority_id,
                "target": rel.target_authority_id,
            },
            ip_address=ip_address,
        )
        await db.delete(rel)
        await db.flush()

    # ------------------------------------------------------------------
    # Wikidata integration
    # ------------------------------------------------------------------

    @staticmethod
    async def wikidata_link(
        db: AsyncSession,
        *,
        record_id: int,
        qid: str,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> AuthorityRecord:
        """Link an authority record to a Wikidata entity and cache enrichment.

        All Wikidata API calls are server-side per CLAUDE.md section 25.5.
        """
        record = await AuthorityService.get(db, record_id=record_id)
        record.wikidata_qid = qid

        enrichment = await AuthorityService._fetch_wikidata_enrichment(qid)
        record.wikidata_enrichment = enrichment
        record.wikidata_last_synced_at = datetime.now(tz=timezone.utc)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="authority_record.wikidata_link",
            resource_type="authority_record",
            resource_id=record.id,
            detail={"qid": qid},
            ip_address=ip_address,
        )
        return record

    @staticmethod
    async def wikidata_unlink(
        db: AsyncSession,
        *,
        record_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> AuthorityRecord:
        """Remove the Wikidata link and cached enrichment."""
        record = await AuthorityService.get(db, record_id=record_id)
        record.wikidata_qid = None
        record.wikidata_enrichment = None
        record.wikidata_last_synced_at = None
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="authority_record.wikidata_unlink",
            resource_type="authority_record",
            resource_id=record.id,
            ip_address=ip_address,
        )
        return record

    @staticmethod
    async def wikidata_fetch(
        db: AsyncSession,
        *,
        record_id: int,
    ) -> dict[str, Any]:
        """Fetch live Wikidata enrichment for a linked authority record.

        Refreshes the cached data if stale (>30 days) or if called on demand.
        """
        record = await AuthorityService.get(db, record_id=record_id)
        if not record.wikidata_qid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authority record is not linked to Wikidata",
            )

        enrichment = await AuthorityService._fetch_wikidata_enrichment(record.wikidata_qid)
        record.wikidata_enrichment = enrichment
        record.wikidata_last_synced_at = datetime.now(tz=timezone.utc)
        await db.flush()
        return enrichment

    @staticmethod
    async def _fetch_wikidata_enrichment(qid: str) -> dict[str, Any]:
        """Call the Wikidata API server-side to retrieve enrichment data.

        Returns a dict with keys matching the table in CLAUDE.md section 25.3.
        """
        url = WIKIDATA_ENTITY_URL.format(qid=qid)
        enrichment: dict[str, Any] = {"qid": qid}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            entity = data.get("entities", {}).get(qid, {})
            claims = entity.get("claims", {})

            # Description
            descriptions = entity.get("descriptions", {})
            if "en" in descriptions:
                enrichment["description"] = descriptions["en"].get("value")

            # Helper to extract the first claim value
            def _claim_value(prop: str) -> str | None:
                vals = claims.get(prop, [])
                if vals:
                    mainsnak = vals[0].get("mainsnak", {}).get("datavalue", {})
                    return mainsnak.get("value") if isinstance(mainsnak.get("value"), str) else None
                return None

            def _claim_time(prop: str) -> str | None:
                vals = claims.get(prop, [])
                if vals:
                    mainsnak = vals[0].get("mainsnak", {}).get("datavalue", {})
                    time_val = mainsnak.get("value", {})
                    if isinstance(time_val, dict):
                        return time_val.get("time")
                return None

            enrichment["birth_date"] = _claim_time("P569")
            enrichment["death_date"] = _claim_time("P570")
            enrichment["viaf_id"] = _claim_value("P214")
            enrichment["lcnaf_id"] = _claim_value("P244")

        except httpx.HTTPError:
            # Non-fatal: return partial enrichment.
            enrichment["error"] = "Failed to fetch data from Wikidata"

        return enrichment
