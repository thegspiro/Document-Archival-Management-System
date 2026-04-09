"""Search service — full-text and faceted search using MySQL MATCH AGAINST."""

from datetime import date
from typing import Any

from sqlalchemy import Select, and_, func, literal_column, or_, select, text, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_authority_link import DocumentAuthorityLink
from app.models.document_file import DocumentFile
from app.models.document_location_link import DocumentLocationLink
from app.models.document_term import DocumentTerm
from app.models.event_document_link import EventDocumentLink


class SearchService:
    """Full-text and faceted search across the document corpus.

    Uses MySQL ``MATCH ... AGAINST`` in natural language mode for full-text
    queries, combined with standard SQL filters for faceted browsing.  The
    version filter (canonical-only) is always applied per CLAUDE.md section 20.5.
    """

    @staticmethod
    async def search(
        db: AsyncSession,
        *,
        q: str | None = None,
        creator_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        term_ids: list[int] | None = None,
        authority_ids: list[int] | None = None,
        location_ids: list[int] | None = None,
        event_ids: list[int] | None = None,
        node_id: int | None = None,
        document_type: str | None = None,
        language: str | None = None,
        review_status: str | None = None,
        is_public: bool | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        """Execute a search query and return paginated results.

        The version filter ensures only canonical versions (or unversioned
        documents) appear in results.
        """
        query: Select = select(Document)

        # ------------------------------------------------------------------
        # Version filter (always applied)
        # ------------------------------------------------------------------
        query = query.where(
            or_(
                Document.version_group_id.is_(None),
                Document.is_canonical_version.is_(True),
            )
        )

        # ------------------------------------------------------------------
        # Full-text search
        # ------------------------------------------------------------------
        if q:
            # MySQL MATCH AGAINST on the documents table FULLTEXT index.
            # This assumes a FULLTEXT index exists on (title, scope_and_content, general_note).
            ft_expr = text(
                "MATCH(documents.title, documents.scope_and_content, documents.general_note) "
                "AGAINST(:q IN NATURAL LANGUAGE MODE)"
            )
            query = query.where(ft_expr.bindparams(q=q))

            # Also search OCR text in document_files and include those document IDs.
            ocr_subq = (
                select(DocumentFile.document_id)
                .where(
                    text(
                        "MATCH(document_files.ocr_text) "
                        "AGAINST(:q_ocr IN NATURAL LANGUAGE MODE)"
                    ).bindparams(q_ocr=q)
                )
            )
            query = query.where(
                or_(
                    ft_expr.bindparams(q=q),
                    Document.id.in_(ocr_subq),
                )
            )

        # ------------------------------------------------------------------
        # Faceted filters
        # ------------------------------------------------------------------
        if creator_id is not None:
            query = query.where(Document.creator_id == creator_id)

        if date_from is not None:
            query = query.where(Document.date_start >= date_from)

        if date_to is not None:
            query = query.where(Document.date_end <= date_to)

        if node_id is not None:
            query = query.where(Document.arrangement_node_id == node_id)

        if review_status is not None:
            query = query.where(Document.review_status == review_status)

        if is_public is not None:
            query = query.where(Document.is_public == is_public)

        if language is not None:
            query = query.where(Document.language_of_material.ilike(f"%{language}%"))

        if document_type is not None:
            from app.models.vocabulary import VocabularyTerm
            type_subq = (
                select(VocabularyTerm.id)
                .where(VocabularyTerm.term == document_type)
            )
            query = query.where(Document.document_type_id.in_(type_subq))

        # Term IDs filter (AND logic — document must have ALL specified terms).
        if term_ids:
            for tid in term_ids:
                term_subq = select(DocumentTerm.document_id).where(
                    DocumentTerm.term_id == tid
                )
                query = query.where(Document.id.in_(term_subq))

        # Authority IDs filter (any role, including creator).
        if authority_ids:
            auth_subq = select(DocumentAuthorityLink.document_id).where(
                DocumentAuthorityLink.authority_id.in_(authority_ids)
            )
            creator_clause = Document.creator_id.in_(authority_ids)
            query = query.where(or_(Document.id.in_(auth_subq), creator_clause))

        # Location IDs filter.
        if location_ids:
            loc_subq = select(DocumentLocationLink.document_id).where(
                DocumentLocationLink.location_id.in_(location_ids)
            )
            query = query.where(Document.id.in_(loc_subq))

        # Event IDs filter.
        if event_ids:
            event_subq = select(EventDocumentLink.document_id).where(
                EventDocumentLink.event_id.in_(event_ids)
            )
            query = query.where(Document.id.in_(event_subq))

        # ------------------------------------------------------------------
        # Count and paginate
        # ------------------------------------------------------------------
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Document.id.desc()).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())

        pages = (total + per_page - 1) // per_page if per_page else 0
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
