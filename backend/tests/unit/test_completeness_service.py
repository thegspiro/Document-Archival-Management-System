"""Unit tests for CompletenessService — compute completeness against institution
standards, missing fields calculation."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.completeness_service import CompletenessService, _DOCUMENT_FIELDS, _LEVELS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_doc(**overrides) -> MagicMock:
    """Return a mock Document with all completeness-relevant fields."""
    doc = MagicMock()
    doc.id = overrides.get("id", 1)
    doc.title = overrides.get("title", "Test Document")
    doc.date_display = overrides.get("date_display", None)
    doc.date_start = overrides.get("date_start", None)
    doc.date_end = overrides.get("date_end", None)
    doc.level_of_description = overrides.get("level_of_description", "item")
    doc.extent = overrides.get("extent", None)
    doc.creator_id = overrides.get("creator_id", None)
    doc.scope_and_content = overrides.get("scope_and_content", None)
    doc.access_conditions = overrides.get("access_conditions", None)
    doc.reproduction_conditions = overrides.get("reproduction_conditions", None)
    doc.language_of_material = overrides.get("language_of_material", None)
    doc.physical_characteristics = overrides.get("physical_characteristics", None)
    doc.archival_history = overrides.get("archival_history", None)
    doc.immediate_source = overrides.get("immediate_source", None)
    doc.finding_aids = overrides.get("finding_aids", None)
    doc.general_note = overrides.get("general_note", None)
    doc.archivists_note = overrides.get("archivists_note", None)
    doc.reference_code = overrides.get("reference_code", None)
    doc.copyright_status = overrides.get("copyright_status", "unknown")
    doc.rights_holder = overrides.get("rights_holder", None)
    doc.description_completeness = "none"
    doc.description_completeness_updated_at = None
    return doc


def _make_mock_standard(level: str, required_fields: list[str]) -> MagicMock:
    """Return a mock InstitutionDescriptionStandard."""
    s = MagicMock()
    s.level = level
    s.required_fields = required_fields
    return s


def _make_db_for_completeness(
    doc: MagicMock,
    standards: dict[str, list[str]],
    term_count: int = 0,
) -> AsyncMock:
    """Build a mocked db session that returns the document, standards, and term count."""
    doc_result = MagicMock()
    doc_result.scalar_one_or_none.return_value = doc

    mock_standards = [
        _make_mock_standard(level, fields) for level, fields in standards.items()
    ]
    standards_result = MagicMock()
    standards_result.scalars.return_value.all.return_value = mock_standards

    term_count_result = MagicMock()
    term_count_result.scalar_one.return_value = term_count

    db = AsyncMock()
    db.execute.side_effect = [doc_result, standards_result, term_count_result]
    return db


# ---------------------------------------------------------------------------
# Completeness levels
# ---------------------------------------------------------------------------


class TestComputeCompleteness:
    """Test compute_completeness for all four levels."""

    @pytest.mark.asyncio
    async def test_none_when_no_standards_and_no_title(self) -> None:
        doc = _make_mock_doc(title="")

        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = doc
        standards_result = MagicMock()
        standards_result.scalars.return_value.all.return_value = []

        db = AsyncMock()
        db.execute.side_effect = [doc_result, standards_result]

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "none"

    @pytest.mark.asyncio
    async def test_minimal_when_no_standards_but_has_title(self) -> None:
        doc = _make_mock_doc(title="Some Title")

        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = doc
        standards_result = MagicMock()
        standards_result.scalars.return_value.all.return_value = []

        db = AsyncMock()
        db.execute.side_effect = [doc_result, standards_result]

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "minimal"

    @pytest.mark.asyncio
    async def test_none_when_minimal_fields_missing(self) -> None:
        # Minimal requires title, date_display, extent — doc has title but not others
        doc = _make_mock_doc(title="Has Title", date_display=None, extent=None)
        standards = {"minimal": ["title", "date_display", "extent"]}
        db = _make_db_for_completeness(doc, standards)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "none"

    @pytest.mark.asyncio
    async def test_minimal_when_all_minimal_fields_present(self) -> None:
        doc = _make_mock_doc(
            title="Complete Letter",
            date_display="January 1, 1920",
            level_of_description="item",
            extent="3 pages",
        )
        standards = {
            "minimal": ["title", "date_display", "level_of_description", "extent"],
        }
        db = _make_db_for_completeness(doc, standards)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "minimal"

    @pytest.mark.asyncio
    async def test_standard_level(self) -> None:
        doc = _make_mock_doc(
            title="Full Letter",
            date_display="1920",
            level_of_description="item",
            extent="3 pages",
            creator_id=5,
            scope_and_content="A letter about municipal affairs.",
            access_conditions="Open",
            language_of_material="eng",
        )
        standards = {
            "minimal": ["title", "date_display", "level_of_description", "extent"],
            "standard": [
                "title", "date_display", "level_of_description", "extent",
                "creator_id", "scope_and_content", "access_conditions",
                "language_of_material",
            ],
        }
        db = _make_db_for_completeness(doc, standards)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "standard"

    @pytest.mark.asyncio
    async def test_full_level_with_terms(self) -> None:
        doc = _make_mock_doc(
            title="Full Letter",
            date_display="1920",
            level_of_description="item",
            extent="3 pages",
            creator_id=5,
            scope_and_content="Description",
            access_conditions="Open",
            language_of_material="eng",
            archival_history="Donated 1965",
            immediate_source="Smith family",
            physical_characteristics="Good condition",
        )
        standards = {
            "minimal": ["title", "date_display"],
            "standard": ["title", "date_display", "creator_id", "scope_and_content"],
            "full": [
                "title", "date_display", "creator_id", "scope_and_content",
                "archival_history", "immediate_source", "physical_characteristics",
                "document_terms",
            ],
        }
        db = _make_db_for_completeness(doc, standards, term_count=3)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "full"

    @pytest.mark.asyncio
    async def test_standard_not_full_when_terms_missing(self) -> None:
        doc = _make_mock_doc(
            title="Letter",
            date_display="1920",
            creator_id=5,
            scope_and_content="Content",
        )
        standards = {
            "minimal": ["title"],
            "standard": ["title", "date_display", "creator_id"],
            "full": ["title", "date_display", "creator_id", "document_terms"],
        }
        # No terms
        db = _make_db_for_completeness(doc, standards, term_count=0)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "standard"

    @pytest.mark.asyncio
    async def test_empty_string_field_treated_as_missing(self) -> None:
        doc = _make_mock_doc(title="Title", date_display="   ")
        standards = {"minimal": ["title", "date_display"]}
        db = _make_db_for_completeness(doc, standards)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "none"

    @pytest.mark.asyncio
    async def test_document_not_found_returns_none(self) -> None:
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = doc_result

        level = await CompletenessService.compute_completeness(db, document_id=999)
        assert level == "none"

    @pytest.mark.asyncio
    async def test_unknown_field_in_standard_treated_as_unsatisfied(self) -> None:
        doc = _make_mock_doc(title="Title")
        standards = {"minimal": ["title", "nonexistent_field"]}
        db = _make_db_for_completeness(doc, standards)

        level = await CompletenessService.compute_completeness(db, document_id=1)
        assert level == "none"


# ---------------------------------------------------------------------------
# Missing fields
# ---------------------------------------------------------------------------


class TestGetMissingFields:
    """Test the get_missing_fields helper that shows what to fill in next."""

    @pytest.mark.asyncio
    async def test_missing_fields_for_empty_document(self) -> None:
        doc = _make_mock_doc(title="Title Only")

        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = doc

        minimal_std = _make_mock_standard("minimal", ["title", "date_display", "extent"])
        standard_std = _make_mock_standard("standard", ["title", "creator_id", "scope_and_content"])
        standards_result = MagicMock()
        standards_result.scalars.return_value.all.return_value = [minimal_std, standard_std]

        term_count_result = MagicMock()
        term_count_result.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [doc_result, standards_result, term_count_result]

        missing = await CompletenessService.get_missing_fields(db, document_id=1)

        assert "date_display" in missing["minimal"]
        assert "extent" in missing["minimal"]
        assert "title" not in missing["minimal"]  # title is present
        assert "creator_id" in missing["standard"]
        assert "scope_and_content" in missing["standard"]

    @pytest.mark.asyncio
    async def test_missing_fields_document_not_found(self) -> None:
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = doc_result

        missing = await CompletenessService.get_missing_fields(db, document_id=999)
        assert missing == {}

    @pytest.mark.asyncio
    async def test_missing_fields_includes_document_terms(self) -> None:
        doc = _make_mock_doc(title="Title")
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = doc

        full_std = _make_mock_standard("full", ["title", "document_terms"])
        standards_result = MagicMock()
        standards_result.scalars.return_value.all.return_value = [full_std]

        term_count_result = MagicMock()
        term_count_result.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [doc_result, standards_result, term_count_result]

        missing = await CompletenessService.get_missing_fields(db, document_id=1)
        assert "document_terms" in missing["full"]

    @pytest.mark.asyncio
    async def test_no_missing_fields_when_fully_described(self) -> None:
        doc = _make_mock_doc(
            title="Full Doc",
            date_display="1920",
        )
        doc_result = MagicMock()
        doc_result.scalar_one_or_none.return_value = doc

        minimal_std = _make_mock_standard("minimal", ["title", "date_display"])
        standards_result = MagicMock()
        standards_result.scalars.return_value.all.return_value = [minimal_std]

        term_count_result = MagicMock()
        term_count_result.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [doc_result, standards_result, term_count_result]

        missing = await CompletenessService.get_missing_fields(db, document_id=1)
        assert missing["minimal"] == []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify the module-level constants are correct."""

    def test_levels_ordering(self) -> None:
        assert _LEVELS == ("minimal", "standard", "full")

    def test_document_fields_contains_key_fields(self) -> None:
        assert "title" in _DOCUMENT_FIELDS
        assert "creator_id" in _DOCUMENT_FIELDS
        assert "scope_and_content" in _DOCUMENT_FIELDS
        assert "date_display" in _DOCUMENT_FIELDS
        assert "extent" in _DOCUMENT_FIELDS
