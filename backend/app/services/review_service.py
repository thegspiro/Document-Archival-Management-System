"""Review service — manage the review queue for documents requiring human review."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.review_queue import ReviewQueue
from app.services.audit_service import AuditService


class ReviewService:
    """Business logic for the document review queue (LLM suggestions,
    manual flags, imports, integrity failures)."""

    @staticmethod
    async def list_queue(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        assigned_to: int | None = None,
        priority: str | None = None,
        reason: str | None = None,
    ) -> dict:
        """Return a paginated, filtered list of review queue items."""
        query = select(ReviewQueue)
        if assigned_to is not None:
            query = query.where(ReviewQueue.assigned_to == assigned_to)
        if priority is not None:
            query = query.where(ReviewQueue.priority == priority)
        if reason is not None:
            query = query.where(ReviewQueue.reason == reason)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(
                # High priority first, then by creation date.
                ReviewQueue.priority.desc(),
                ReviewQueue.created_at.asc(),
            )
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def get_item(db: AsyncSession, *, document_id: int) -> ReviewQueue:
        """Return the review queue item for a specific document, or raise 404."""
        result = await db.execute(
            select(ReviewQueue).where(ReviewQueue.document_id == document_id)
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review queue item not found",
            )
        return item

    @staticmethod
    async def approve(
        db: AsyncSession,
        *,
        document_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Document:
        """Approve a document in the review queue.

        Sets ``review_status`` to ``'approved'`` and removes the queue item.
        """
        item = await ReviewService.get_item(db, document_id=document_id)

        # Update the document record.
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        doc.review_status = "approved"
        await db.delete(item)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="review.approve",
            resource_type="document",
            resource_id=document_id,
            detail={"reason": item.reason},
            ip_address=ip_address,
        )
        return doc

    @staticmethod
    async def reject(
        db: AsyncSession,
        *,
        document_id: int,
        notes: str | None = None,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Document:
        """Reject a document in the review queue.

        Sets ``review_status`` to ``'rejected'`` and removes the queue item.
        """
        item = await ReviewService.get_item(db, document_id=document_id)

        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        doc.review_status = "rejected"
        if notes:
            doc.review_notes = notes
        await db.delete(item)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="review.reject",
            resource_type="document",
            resource_id=document_id,
            detail={"reason": item.reason, "notes": notes},
            ip_address=ip_address,
        )
        return doc

    @staticmethod
    async def assign(
        db: AsyncSession,
        *,
        document_id: int,
        assigned_to: int | None,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ReviewQueue:
        """Assign (or unassign) a review queue item to a specific user."""
        item = await ReviewService.get_item(db, document_id=document_id)
        item.assigned_to = assigned_to
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="review.assign",
            resource_type="review_queue",
            resource_id=item.id,
            detail={"document_id": document_id, "assigned_to": assigned_to},
            ip_address=ip_address,
        )
        return item
