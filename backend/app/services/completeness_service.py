"""Completeness service — compute description completeness against institution
standards.

The completeness level is recomputed after every save to a document's descriptive
fields, after tag changes, and as a nightly batch job.  It evaluates the document
against each level in ascending order and sets ``description_completeness`` to the
highest level whose required fields are all satisfied.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_term import DocumentTerm
from app.models.institution_description_standard import InstitutionDescriptionStandard


# Fields that can be checked on the Document model directly.
_DOCUMENT_FIELDS = {
    "title", "date_display", "date_start", "date_end", "level_of_description",
    "extent", "creator_id", "scope_and_content", "access_conditions",
    "reproduction_conditions", "language_of_material", "physical_characteristics",
    "archival_history", "immediate_source", "finding_aids", "general_note",
    "archivists_note", "reference_code", "copyright_status", "rights_holder",
}

# The ordered levels from lowest to highest.
_LEVELS = ("minimal", "standard", "full")


class CompletenessService:
    """Evaluates how completely a document has been described against the
    institution's configurable standards."""

    @staticmethod
    async def compute_completeness(
        db: AsyncSession,
        *,
        document_id: int,
    ) -> str:
        """Recompute and persist the completeness level for a single document.

        Returns the computed level string: ``'none'``, ``'minimal'``,
        ``'standard'``, or ``'full'``.
        """
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            return "none"

        # Load institution standards (one row per level).
        standards_result = await db.execute(
            select(InstitutionDescriptionStandard).order_by(
                InstitutionDescriptionStandard.level
            )
        )
        standards = {s.level: s for s in standards_result.scalars().all()}

        # If no standards are configured, fall back to title-only = none.
        if not standards:
            computed = "none" if not doc.title else "minimal"
            await CompletenessService._persist(db, doc, computed)
            return computed

        # Check whether the document has any terms (used for standards that
        # require at least one tag/term).
        term_count_result = await db.execute(
            select(func.count(DocumentTerm.id)).where(
                DocumentTerm.document_id == document_id
            )
        )
        has_terms = term_count_result.scalar_one() > 0

        computed_level = "none"

        for level in _LEVELS:
            standard = standards.get(level)
            if standard is None:
                continue

            required_fields: list[str] = standard.required_fields or []
            all_satisfied = True

            for field_name in required_fields:
                if field_name == "document_terms":
                    # Special case: at least one term must be linked.
                    if not has_terms:
                        all_satisfied = False
                        break
                elif field_name in _DOCUMENT_FIELDS and hasattr(doc, field_name):
                    value = getattr(doc, field_name)
                    if value is None or (isinstance(value, str) and not value.strip()):
                        all_satisfied = False
                        break
                else:
                    # Unknown field name in the standard — treat as unsatisfied
                    # to be safe (correctness over speed).
                    all_satisfied = False
                    break

            if all_satisfied:
                computed_level = level
            else:
                # Stop checking higher levels; they include stricter requirements.
                break

        await CompletenessService._persist(db, doc, computed_level)
        return computed_level

    @staticmethod
    async def _persist(
        db: AsyncSession,
        doc: Document,
        level: str,
    ) -> None:
        """Write the computed completeness level back to the document."""
        doc.description_completeness = level
        doc.description_completeness_updated_at = datetime.now(tz=timezone.utc)
        await db.flush()

    @staticmethod
    async def get_missing_fields(
        db: AsyncSession,
        *,
        document_id: int,
    ) -> dict[str, list[str]]:
        """Return, for each completeness level, the fields that are still
        missing.  Useful for showing the archivist what to fill in next.
        """
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            return {}

        standards_result = await db.execute(
            select(InstitutionDescriptionStandard)
        )
        standards = {s.level: s for s in standards_result.scalars().all()}

        term_count_result = await db.execute(
            select(func.count(DocumentTerm.id)).where(
                DocumentTerm.document_id == document_id
            )
        )
        has_terms = term_count_result.scalar_one() > 0

        missing: dict[str, list[str]] = {}

        for level in _LEVELS:
            standard = standards.get(level)
            if standard is None:
                continue

            level_missing: list[str] = []
            required_fields: list[str] = standard.required_fields or []

            for field_name in required_fields:
                if field_name == "document_terms":
                    if not has_terms:
                        level_missing.append("document_terms")
                elif field_name in _DOCUMENT_FIELDS and hasattr(doc, field_name):
                    value = getattr(doc, field_name)
                    if value is None or (isinstance(value, str) and not value.strip()):
                        level_missing.append(field_name)
                else:
                    level_missing.append(field_name)

            missing[level] = level_missing

        return missing
