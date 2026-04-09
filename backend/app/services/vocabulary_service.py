"""Vocabulary service — CRUD for domains and terms, term merging."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_term import DocumentTerm
from app.models.vocabulary import VocabularyDomain, VocabularyTerm
from app.services.audit_service import AuditService


class VocabularyService:
    """Business logic for the controlled vocabulary system."""

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------

    @staticmethod
    async def create_domain(
        db: AsyncSession,
        *,
        name: str,
        description: str | None = None,
        allows_user_addition: bool = True,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> VocabularyDomain:
        """Create a vocabulary domain.  Raises 409 on duplicate name."""
        existing = await db.execute(
            select(VocabularyDomain).where(VocabularyDomain.name == name)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Domain '{name}' already exists",
            )

        domain = VocabularyDomain(
            name=name,
            description=description,
            allows_user_addition=allows_user_addition,
        )
        db.add(domain)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="vocabulary_domain.create",
            resource_type="vocabulary_domain",
            resource_id=domain.id,
            detail={"name": name},
            ip_address=ip_address,
        )
        return domain

    @staticmethod
    async def get_domain(db: AsyncSession, *, domain_id: int) -> VocabularyDomain:
        """Return a domain by ID or raise 404."""
        result = await db.execute(
            select(VocabularyDomain).where(VocabularyDomain.id == domain_id)
        )
        domain = result.scalar_one_or_none()
        if domain is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary domain not found",
            )
        return domain

    @staticmethod
    async def list_domains(db: AsyncSession) -> list[VocabularyDomain]:
        """Return all vocabulary domains."""
        result = await db.execute(
            select(VocabularyDomain).order_by(VocabularyDomain.name)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Terms
    # ------------------------------------------------------------------

    @staticmethod
    async def create_term(
        db: AsyncSession,
        *,
        domain_id: int,
        term: str,
        definition: str | None = None,
        broader_term_id: int | None = None,
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> VocabularyTerm:
        """Create a vocabulary term within a domain.

        Raises 409 if the term already exists in the same domain.
        """
        # Verify domain exists.
        await VocabularyService.get_domain(db, domain_id=domain_id)

        existing = await db.execute(
            select(VocabularyTerm).where(
                VocabularyTerm.domain_id == domain_id,
                VocabularyTerm.term == term,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Term '{term}' already exists in this domain",
            )

        vt = VocabularyTerm(
            domain_id=domain_id,
            term=term,
            definition=definition,
            broader_term_id=broader_term_id,
            created_by=created_by,
        )
        db.add(vt)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="vocabulary_term.create",
            resource_type="vocabulary_term",
            resource_id=vt.id,
            detail={"domain_id": domain_id, "term": term},
            ip_address=ip_address,
        )
        return vt

    @staticmethod
    async def get_term(db: AsyncSession, *, term_id: int) -> VocabularyTerm:
        """Return a term by ID or raise 404."""
        result = await db.execute(
            select(VocabularyTerm).where(VocabularyTerm.id == term_id)
        )
        term = result.scalar_one_or_none()
        if term is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary term not found",
            )
        return term

    @staticmethod
    async def list_terms(
        db: AsyncSession,
        *,
        domain_id: int,
        active_only: bool = True,
    ) -> list[VocabularyTerm]:
        """Return all terms in a domain, ordered by sort_order then term."""
        query = select(VocabularyTerm).where(VocabularyTerm.domain_id == domain_id)
        if active_only:
            query = query.where(VocabularyTerm.is_active.is_(True))
        result = await db.execute(
            query.order_by(VocabularyTerm.sort_order, VocabularyTerm.term)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_term(
        db: AsyncSession,
        *,
        term_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> VocabularyTerm:
        """Update a vocabulary term's mutable fields."""
        term = await VocabularyService.get_term(db, term_id=term_id)

        protected = {"id", "domain_id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(term, key):
                setattr(term, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="vocabulary_term.update",
            resource_type="vocabulary_term",
            resource_id=term.id,
            detail=changes,
            ip_address=ip_address,
        )
        return term

    @staticmethod
    async def delete_term(
        db: AsyncSession,
        *,
        term_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Soft-delete a vocabulary term by setting ``is_active = False``."""
        term = await VocabularyService.get_term(db, term_id=term_id)
        term.is_active = False
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="vocabulary_term.delete",
            resource_type="vocabulary_term",
            resource_id=term.id,
            detail={"term": term.term},
            ip_address=ip_address,
        )

    # ------------------------------------------------------------------
    # Term merging (bulk correction)
    # ------------------------------------------------------------------

    @staticmethod
    async def merge_term(
        db: AsyncSession,
        *,
        source_term_id: int,
        target_term_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> int:
        """Merge term A (source) into term B (target).

        Steps per CLAUDE.md section 5.8:
        1. Update all ``document_terms`` rows from source to target.
        2. Delete the source term.
        3. Write an audit_log entry recording the merge.

        Returns the number of document_terms rows affected.
        """
        if source_term_id == target_term_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot merge a term into itself",
            )

        source = await VocabularyService.get_term(db, term_id=source_term_id)
        target = await VocabularyService.get_term(db, term_id=target_term_id)

        if source.domain_id != target.domain_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot merge terms from different domains",
            )

        # Count affected rows before the update.
        count_result = await db.execute(
            select(func.count(DocumentTerm.id)).where(
                DocumentTerm.term_id == source_term_id
            )
        )
        affected_count = count_result.scalar_one()

        # 1. Reassign document_terms.  Handle potential duplicates by deleting
        #    rows that would violate the unique constraint after the update.
        existing_target_docs = await db.execute(
            select(DocumentTerm.document_id).where(DocumentTerm.term_id == target_term_id)
        )
        target_doc_ids = {row[0] for row in existing_target_docs.all()}

        # Delete source rows that would become duplicates.
        if target_doc_ids:
            from sqlalchemy import delete
            await db.execute(
                delete(DocumentTerm).where(
                    DocumentTerm.term_id == source_term_id,
                    DocumentTerm.document_id.in_(target_doc_ids),
                )
            )

        # Update remaining source rows to target.
        await db.execute(
            update(DocumentTerm)
            .where(DocumentTerm.term_id == source_term_id)
            .values(term_id=target_term_id)
        )

        # 2. Delete the source term.
        await db.delete(source)
        await db.flush()

        # 3. Audit log.
        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="vocabulary_term.merge",
            resource_type="vocabulary_term",
            resource_id=target_term_id,
            detail={
                "merged_term_id": source_term_id,
                "merged_term": source.term,
                "into_term_id": target_term_id,
                "into_term": target.term,
                "documents_affected": affected_count,
            },
            ip_address=ip_address,
        )
        return affected_count
