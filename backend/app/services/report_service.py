"""Report service — structured reporting for accessions, processing, users,
collections, and public access.

All reports are accessible to users with at minimum ``archivist`` role.
Admins see all collections; archivists see only their accessible collections.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.exhibition import Exhibition
from app.models.audit_log import AuditLog


class ReportService:
    """Generates structured report data.  Each method returns a dict suitable
    for direct JSON serialisation or conversion to CSV/PDF by the router."""

    # ------------------------------------------------------------------
    # Accession report
    # ------------------------------------------------------------------

    @staticmethod
    async def accessions_report(
        db: AsyncSession,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        node_id: int | None = None,
        created_by: int | None = None,
    ) -> dict[str, Any]:
        """New accessions by date range.

        Shows accession numbers, titles, date accessioned, collection,
        and description completeness level.
        """
        query = select(
            Document.id,
            Document.accession_number,
            Document.title,
            Document.created_at,
            Document.arrangement_node_id,
            Document.description_completeness,
            Document.created_by,
        )

        if date_from:
            query = query.where(Document.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.where(Document.created_at <= datetime.combine(date_to, datetime.max.time()))
        if node_id:
            query = query.where(Document.arrangement_node_id == node_id)
        if created_by:
            query = query.where(Document.created_by == created_by)

        result = await db.execute(query.order_by(Document.created_at.desc()))
        rows = result.all()

        items = [
            {
                "id": r.id,
                "accession_number": r.accession_number,
                "title": r.title,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "arrangement_node_id": r.arrangement_node_id,
                "description_completeness": r.description_completeness,
                "created_by": r.created_by,
            }
            for r in rows
        ]
        return {"report": "accessions", "total": len(items), "items": items}

    # ------------------------------------------------------------------
    # Processing progress report
    # ------------------------------------------------------------------

    @staticmethod
    async def processing_report(
        db: AsyncSession,
        *,
        node_id: int | None = None,
    ) -> dict[str, Any]:
        """Per-collection breakdown of documents at each completeness level.

        Returns counts and percentages for none / minimal / standard / full.
        """
        query = select(
            Document.arrangement_node_id,
            Document.description_completeness,
            func.count(Document.id).label("count"),
        ).group_by(
            Document.arrangement_node_id,
            Document.description_completeness,
        )

        if node_id:
            query = query.where(Document.arrangement_node_id == node_id)

        result = await db.execute(query)
        rows = result.all()

        # Aggregate into per-node summaries.
        nodes: dict[int | None, dict[str, int]] = {}
        for r in rows:
            nid = r.arrangement_node_id
            if nid not in nodes:
                nodes[nid] = {"none": 0, "minimal": 0, "standard": 0, "full": 0, "total": 0}
            level = r.description_completeness or "none"
            nodes[nid][level] = r.count
            nodes[nid]["total"] += r.count

        items = []
        for nid, counts in nodes.items():
            total = counts["total"]
            items.append({
                "arrangement_node_id": nid,
                "total": total,
                "none": counts["none"],
                "minimal": counts["minimal"],
                "standard": counts["standard"],
                "full": counts["full"],
                "pct_none": round(counts["none"] / total * 100, 1) if total else 0,
                "pct_minimal": round(counts["minimal"] / total * 100, 1) if total else 0,
                "pct_standard": round(counts["standard"] / total * 100, 1) if total else 0,
                "pct_full": round(counts["full"] / total * 100, 1) if total else 0,
            })

        return {"report": "processing", "total_collections": len(items), "items": items}

    # ------------------------------------------------------------------
    # User activity report
    # ------------------------------------------------------------------

    @staticmethod
    async def users_report(
        db: AsyncSession,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """Per-user counts of documents created and updated."""
        filters = []
        if date_from:
            filters.append(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            filters.append(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))
        if user_id:
            filters.append(AuditLog.user_id == user_id)

        # Documents created.
        create_q = (
            select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("count"),
            )
            .where(
                AuditLog.action == "document.create",
                *filters,
            )
            .group_by(AuditLog.user_id)
        )
        create_result = await db.execute(create_q)
        creates = {r.user_id: r.count for r in create_result.all()}

        # Documents updated.
        update_q = (
            select(
                AuditLog.user_id,
                func.count(AuditLog.id).label("count"),
            )
            .where(
                AuditLog.action == "document.update",
                *filters,
            )
            .group_by(AuditLog.user_id)
        )
        update_result = await db.execute(update_q)
        updates = {r.user_id: r.count for r in update_result.all()}

        all_user_ids = set(creates.keys()) | set(updates.keys())
        items = [
            {
                "user_id": uid,
                "documents_created": creates.get(uid, 0),
                "documents_updated": updates.get(uid, 0),
            }
            for uid in sorted(all_user_ids)
        ]

        return {"report": "users", "total_users": len(items), "items": items}

    # ------------------------------------------------------------------
    # Collection summary report
    # ------------------------------------------------------------------

    @staticmethod
    async def collection_report(
        db: AsyncSession,
        *,
        node_id: int | None = None,
    ) -> dict[str, Any]:
        """Total documents, files, storage used, OCR completion, and public
        percentage for a collection or the entire repository.
        """
        doc_query = select(Document)
        if node_id:
            doc_query = doc_query.where(Document.arrangement_node_id == node_id)

        total_docs = (await db.execute(
            select(func.count()).select_from(doc_query.subquery())
        )).scalar_one()

        public_docs = (await db.execute(
            select(func.count(Document.id)).where(
                Document.is_public.is_(True),
                Document.arrangement_node_id == node_id if node_id else True,
            )
        )).scalar_one()

        # File stats.
        file_query = select(DocumentFile)
        if node_id:
            file_query = file_query.join(Document).where(
                Document.arrangement_node_id == node_id
            )

        total_files = (await db.execute(
            select(func.count()).select_from(file_query.subquery())
        )).scalar_one()

        storage_bytes_result = await db.execute(
            select(func.sum(DocumentFile.file_size_bytes))
        )
        storage_bytes = storage_bytes_result.scalar_one() or 0

        ocr_complete = (await db.execute(
            select(func.count(DocumentFile.id)).where(
                DocumentFile.ocr_status == "complete"
            )
        )).scalar_one()

        return {
            "report": "collection",
            "arrangement_node_id": node_id,
            "total_documents": total_docs,
            "total_files": total_files,
            "total_storage_bytes": int(storage_bytes),
            "public_documents": public_docs,
            "pct_public": round(public_docs / total_docs * 100, 1) if total_docs else 0,
            "ocr_complete": ocr_complete,
            "pct_ocr_complete": round(ocr_complete / total_files * 100, 1) if total_files else 0,
        }

    # ------------------------------------------------------------------
    # Public access summary
    # ------------------------------------------------------------------

    @staticmethod
    async def public_access_report(
        db: AsyncSession,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, Any]:
        """Documents and exhibitions published within the date range."""
        doc_query = select(func.count(Document.id)).where(Document.is_public.is_(True))
        if date_from:
            doc_query = doc_query.where(
                Document.updated_at >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to:
            doc_query = doc_query.where(
                Document.updated_at <= datetime.combine(date_to, datetime.max.time())
            )
        published_docs = (await db.execute(doc_query)).scalar_one()

        exhibit_query = select(func.count(Exhibition.id)).where(Exhibition.is_published.is_(True))
        if date_from:
            exhibit_query = exhibit_query.where(
                Exhibition.published_at >= datetime.combine(date_from, datetime.min.time())
            )
        if date_to:
            exhibit_query = exhibit_query.where(
                Exhibition.published_at <= datetime.combine(date_to, datetime.max.time())
            )
        published_exhibits = (await db.execute(exhibit_query)).scalar_one()

        return {
            "report": "public_access",
            "published_documents": published_docs,
            "published_exhibitions": published_exhibits,
        }
