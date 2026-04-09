"""Preservation service — event logging, fixity checks, and format inventory.

Implements OAIS and PREMIS requirements for digital preservation.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document_file import DocumentFile
from app.models.fixity_check import FixityCheck
from app.models.preservation_event import PreservationEvent
from app.models.review_queue import ReviewQueue
from app.services.audit_service import AuditService


class PreservationService:
    """Preservation operations: event logging, fixity verification, and
    format inventory reporting."""

    # ------------------------------------------------------------------
    # Preservation event logging
    # ------------------------------------------------------------------

    @staticmethod
    async def log_event(
        db: AsyncSession,
        *,
        document_file_id: int | None = None,
        document_id: int | None = None,
        event_type: str,
        event_outcome: str,
        event_detail: str | None = None,
        agent: str | None = None,
    ) -> PreservationEvent:
        """Write an immutable preservation event row."""
        event = PreservationEvent(
            document_file_id=document_file_id,
            document_id=document_id,
            event_type=event_type,
            event_outcome=event_outcome,
            event_detail=event_detail,
            agent=agent,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_events_for_document(
        db: AsyncSession,
        *,
        document_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return paginated preservation events for a document."""
        query = select(PreservationEvent).where(
            PreservationEvent.document_id == document_id
        )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(PreservationEvent.event_datetime.desc())
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    # ------------------------------------------------------------------
    # Fixity checks
    # ------------------------------------------------------------------

    @staticmethod
    async def run_fixity_check(
        db: AsyncSession,
        *,
        document_file_id: int,
        checked_by: str = "manual",
    ) -> FixityCheck:
        """Run a fixity check on a single file by recomputing the SHA-256 hash
        and comparing it to the stored hash.

        On mismatch or missing file:
        1. Write a ``preservation_events`` row with outcome ``'failure'``.
        2. Create a ``review_queue`` entry with reason ``integrity_failure``, priority ``high``.
        """
        result = await db.execute(
            select(DocumentFile).where(DocumentFile.id == document_file_id)
        )
        doc_file = result.scalar_one_or_none()
        if doc_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found",
            )

        stored_hash = doc_file.file_hash_sha256 or ""
        file_path = Path(settings.STORAGE_ROOT) / doc_file.stored_path

        if not file_path.exists():
            outcome = "file_missing"
            computed_hash = ""
        else:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            computed_hash = h.hexdigest()
            outcome = "match" if computed_hash == stored_hash else "mismatch"

        check = FixityCheck(
            document_file_id=document_file_id,
            stored_hash=stored_hash,
            computed_hash=computed_hash,
            outcome=outcome,
            checked_by=checked_by,
        )
        db.add(check)
        await db.flush()

        # Preservation event.
        event_outcome = "success" if outcome == "match" else "failure"
        await PreservationService.log_event(
            db,
            document_file_id=document_file_id,
            document_id=doc_file.document_id,
            event_type="fixity_check",
            event_outcome=event_outcome,
            event_detail=f"Fixity {outcome}: stored={stored_hash}, computed={computed_hash}",
            agent=checked_by,
        )

        # On failure: create review queue entry.
        if outcome != "match":
            existing_review = await db.execute(
                select(ReviewQueue).where(ReviewQueue.document_id == doc_file.document_id)
            )
            if existing_review.scalar_one_or_none() is None:
                db.add(ReviewQueue(
                    document_id=doc_file.document_id,
                    reason="integrity_failure",
                    priority="high",
                    notes=f"Fixity check {outcome} for file {doc_file.filename}",
                ))
                await db.flush()

        return check

    # ------------------------------------------------------------------
    # Fixity report
    # ------------------------------------------------------------------

    @staticmethod
    async def get_fixity_report(db: AsyncSession) -> dict[str, Any]:
        """Return a summary of fixity check outcomes."""
        total_result = await db.execute(
            select(func.count(FixityCheck.id))
        )
        total = total_result.scalar_one()

        match_result = await db.execute(
            select(func.count(FixityCheck.id)).where(FixityCheck.outcome == "match")
        )
        matches = match_result.scalar_one()

        mismatch_result = await db.execute(
            select(func.count(FixityCheck.id)).where(FixityCheck.outcome == "mismatch")
        )
        mismatches = mismatch_result.scalar_one()

        missing_result = await db.execute(
            select(func.count(FixityCheck.id)).where(FixityCheck.outcome == "file_missing")
        )
        missing = missing_result.scalar_one()

        # Latest check timestamp.
        latest_result = await db.execute(
            select(func.max(FixityCheck.checked_at))
        )
        latest = latest_result.scalar_one()

        return {
            "total_checks": total,
            "matches": matches,
            "mismatches": mismatches,
            "files_missing": missing,
            "last_check_at": latest.isoformat() if latest else None,
        }

    # ------------------------------------------------------------------
    # Format inventory
    # ------------------------------------------------------------------

    @staticmethod
    async def get_format_inventory(db: AsyncSession) -> list[dict[str, Any]]:
        """Return the distribution of file formats across the repository.

        Groups by PRONOM PUID and format name, returning counts and total
        size per format.
        """
        result = await db.execute(
            select(
                DocumentFile.format_puid,
                DocumentFile.format_name,
                func.count(DocumentFile.id).label("file_count"),
                func.sum(DocumentFile.file_size_bytes).label("total_bytes"),
            )
            .group_by(DocumentFile.format_puid, DocumentFile.format_name)
            .order_by(func.count(DocumentFile.id).desc())
        )
        rows = result.all()
        return [
            {
                "format_puid": row.format_puid,
                "format_name": row.format_name,
                "file_count": row.file_count,
                "total_bytes": int(row.total_bytes) if row.total_bytes else 0,
            }
            for row in rows
        ]
