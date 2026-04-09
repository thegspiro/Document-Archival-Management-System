"""Document service — CRUD, inbox, accession number generation, and bulk actions."""

from datetime import date, datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import Select, and_, delete, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_term import DocumentTerm
from app.models.review_queue import ReviewQueue
from app.models.sequence import Sequence
from app.models.system_setting import SystemSetting
from app.services.audit_service import AuditService


class DocumentService:
    """Business logic for documents — the core archival item record."""

    # ------------------------------------------------------------------
    # Accession number generation
    # ------------------------------------------------------------------

    @staticmethod
    async def _generate_accession_number(db: AsyncSession) -> str:
        """Atomically generate the next accession number using the sequences
        table with ``SELECT ... FOR UPDATE`` to prevent gaps or collisions.
        """
        year = datetime.now(tz=timezone.utc).year
        seq_name = f"accession_{year}"

        # Fetch or create the sequence row with a row-level lock.
        result = await db.execute(
            select(Sequence)
            .where(Sequence.name == seq_name)
            .with_for_update()
        )
        seq = result.scalar_one_or_none()

        if seq is None:
            seq = Sequence(name=seq_name, current_value=0)
            db.add(seq)
            await db.flush()
            # Re-acquire with lock after insert.
            result = await db.execute(
                select(Sequence)
                .where(Sequence.name == seq_name)
                .with_for_update()
            )
            seq = result.scalar_one()

        seq.current_value += 1
        next_val = seq.current_value
        await db.flush()

        # Read the configurable format from system_settings; fall back to default.
        fmt_result = await db.execute(
            select(SystemSetting.value).where(
                SystemSetting.key == "accession.format"
            )
        )
        fmt_row = fmt_result.scalar_one_or_none()
        fmt = "{YEAR}-{SEQUENCE:04d}"
        if fmt_row and isinstance(fmt_row, dict) and "format" in fmt_row:
            fmt = fmt_row["format"]

        accession = fmt.replace("{YEAR}", str(year)).replace(
            "{SEQUENCE:04d}", f"{next_val:04d}"
        ).replace("{SEQUENCE}", str(next_val))

        return accession

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_document(
        db: AsyncSession,
        *,
        data: dict[str, Any],
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> Document:
        """Create a new document record, auto-assigning an accession number
        if one is not provided.
        """
        if not data.get("accession_number"):
            data["accession_number"] = await DocumentService._generate_accession_number(db)

        data.setdefault("created_by", created_by)

        doc = Document(**data)
        db.add(doc)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="document.create",
            resource_type="document",
            resource_id=doc.id,
            detail={"title": doc.title, "accession_number": doc.accession_number},
            ip_address=ip_address,
        )
        return doc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    async def get_document(db: AsyncSession, *, document_id: int) -> Document:
        """Return a single document by ID, or raise 404."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )
        return doc

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        node_id: int | None = None,
        creator_id: int | None = None,
        is_public: bool | None = None,
        review_status: str | None = None,
        inbox_status: str | None = None,
        accession_number: str | None = None,
    ) -> dict:
        """Return a paginated, filtered list of documents.

        Only canonical versions (or unversioned documents) are returned
        unless an explicit ``accession_number`` lookup is provided.
        """
        query: Select = select(Document)

        # Version filter — always applied unless doing an exact accession lookup.
        if accession_number:
            query = query.where(Document.accession_number == accession_number)
        else:
            query = query.where(
                or_(
                    Document.version_group_id.is_(None),
                    Document.is_canonical_version.is_(True),
                )
            )

        if node_id is not None:
            query = query.where(Document.arrangement_node_id == node_id)
        if creator_id is not None:
            query = query.where(Document.creator_id == creator_id)
        if is_public is not None:
            query = query.where(Document.is_public == is_public)
        if review_status is not None:
            query = query.where(Document.review_status == review_status)
        if inbox_status is not None:
            query = query.where(Document.inbox_status == inbox_status)

        # Total count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        # Paginated results
        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Document.id.desc()).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())

        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    # ------------------------------------------------------------------
    # Inbox
    # ------------------------------------------------------------------

    @staticmethod
    async def get_inbox_documents(
        db: AsyncSession,
        *,
        user_id: int | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return documents with ``inbox_status='inbox'``."""
        return await DocumentService.list_documents(
            db, page=page, per_page=per_page, inbox_status="inbox"
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_document(
        db: AsyncSession,
        *,
        document_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Document:
        """Update mutable fields on a document."""
        doc = await DocumentService.get_document(db, document_id=document_id)

        # Fields that must never be set directly by callers.
        protected = {
            "id", "created_at", "updated_at", "created_by",
            "description_completeness", "description_completeness_updated_at",
        }
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(doc, key):
                old_value = getattr(doc, key)
                setattr(doc, key, value)
                changes[key] = {"old": str(old_value), "new": str(value)}

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="document.update",
            resource_type="document",
            resource_id=doc.id,
            detail=changes,
            ip_address=ip_address,
        )
        return doc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        *,
        document_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete a document record.

        In practice, documents should go through the deaccession workflow
        rather than a bare delete.  This method is provided for admin use.
        """
        doc = await DocumentService.get_document(db, document_id=document_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="document.delete",
            resource_type="document",
            resource_id=doc.id,
            detail={
                "title": doc.title,
                "accession_number": doc.accession_number,
            },
            ip_address=ip_address,
        )

        await db.delete(doc)
        await db.flush()

    # ------------------------------------------------------------------
    # Bulk actions
    # ------------------------------------------------------------------

    @staticmethod
    async def bulk_action(
        db: AsyncSession,
        *,
        document_ids: list[int],
        action_type: str,
        term_ids: list[int] | None = None,
        node_id: int | None = None,
        is_public: bool | None = None,
        reason: str | None = None,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> int:
        """Execute a bulk action on the given document IDs.

        Returns the count of documents affected.
        """
        affected = 0

        if action_type == "apply_terms":
            if not term_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="term_ids required for apply_terms",
                )
            for doc_id in document_ids:
                for term_id in term_ids:
                    existing = await db.execute(
                        select(DocumentTerm).where(
                            DocumentTerm.document_id == doc_id,
                            DocumentTerm.term_id == term_id,
                        )
                    )
                    if existing.scalar_one_or_none() is None:
                        db.add(DocumentTerm(
                            document_id=doc_id,
                            term_id=term_id,
                            created_by=acting_user_id,
                        ))
            affected = len(document_ids)
            await db.flush()

        elif action_type == "remove_terms":
            if not term_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="term_ids required for remove_terms",
                )
            for doc_id in document_ids:
                await db.execute(
                    delete(DocumentTerm).where(
                        DocumentTerm.document_id == doc_id,
                        DocumentTerm.term_id.in_(term_ids),
                    )
                )
            affected = len(document_ids)
            await db.flush()

        elif action_type == "assign_node":
            if node_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="node_id required for assign_node",
                )
            await db.execute(
                update(Document)
                .where(Document.id.in_(document_ids))
                .values(arrangement_node_id=node_id)
            )
            affected = len(document_ids)
            await db.flush()

        elif action_type == "set_public":
            if is_public is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="is_public required for set_public",
                )
            await db.execute(
                update(Document)
                .where(Document.id.in_(document_ids))
                .values(is_public=is_public)
            )
            affected = len(document_ids)
            await db.flush()

        elif action_type == "clear_inbox":
            await db.execute(
                update(Document)
                .where(Document.id.in_(document_ids))
                .values(inbox_status="processed")
            )
            affected = len(document_ids)
            await db.flush()

        elif action_type == "add_to_review":
            for doc_id in document_ids:
                existing = await db.execute(
                    select(ReviewQueue).where(ReviewQueue.document_id == doc_id)
                )
                if existing.scalar_one_or_none() is None:
                    db.add(ReviewQueue(
                        document_id=doc_id,
                        reason="manual_flag",
                        created_by=acting_user_id,
                    ))
                    affected += 1
            await db.flush()

        elif action_type == "delete":
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="reason required for delete action",
                )
            for doc_id in document_ids:
                await DocumentService.delete_document(
                    db,
                    document_id=doc_id,
                    acting_user_id=acting_user_id,
                    ip_address=ip_address,
                )
                affected += 1

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown bulk action type: {action_type}",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action=f"document.bulk.{action_type}",
            resource_type="document",
            detail={
                "document_ids": document_ids,
                "action_type": action_type,
                "affected": affected,
            },
            ip_address=ip_address,
        )

        return affected
