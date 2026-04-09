"""Unit tests for citation formatters — Chicago note/bib, Turabian, BibTeX, RIS,
CSL-JSON, and version information handling."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.export.citations import (
    document_to_csl_json,
    format_bibtex,
    format_chicago_bib,
    format_chicago_note,
    format_ris,
    format_turabian,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_doc(**overrides) -> MagicMock:
    """Build a mock Document with citation-relevant fields."""
    doc = MagicMock()
    doc.id = overrides.get("id", 1)
    doc.title = overrides.get("title", "Test Document")
    doc.accession_number = overrides.get("accession_number", "2025-0042")
    doc.date_display = overrides.get("date_display", None)
    doc.date_start = overrides.get("date_start", None)
    doc.scope_and_content = overrides.get("scope_and_content", None)
    doc.language_of_material = overrides.get("language_of_material", None)
    doc.original_location = overrides.get("original_location", None)
    doc.version_group_id = overrides.get("version_group_id", None)
    doc.version_number = overrides.get("version_number", 1)
    doc.version_label = overrides.get("version_label", None)

    # Creator as an authority record
    creator = overrides.get("creator", None)
    if creator is None:
        doc.creator = None
    else:
        mock_creator = MagicMock()
        mock_creator.authorized_name = creator
        doc.creator = mock_creator

    return doc


# ---------------------------------------------------------------------------
# CSL-JSON
# ---------------------------------------------------------------------------


class TestCSLJSON:
    """Test document_to_csl_json for all field mappings."""

    def test_basic_fields(self) -> None:
        doc = _make_mock_doc(
            title="City Council Minutes",
            accession_number="2025-0001",
            creator="John Smith",
        )
        csl = document_to_csl_json(doc, institution_name="Falls Church VFD Archives")

        assert csl["title"] == "City Council Minutes"
        assert csl["type"] == "manuscript"
        assert csl["archive"] == "Falls Church VFD Archives"
        assert csl["call-number"] == "2025-0001"
        assert csl["author"] == [{"literal": "John Smith"}]

    def test_no_creator(self) -> None:
        doc = _make_mock_doc(creator=None)
        csl = document_to_csl_json(doc)
        assert "author" not in csl

    def test_date_start_date_parts(self) -> None:
        doc = _make_mock_doc(date_start=date(1920, 3, 15))
        csl = document_to_csl_json(doc)
        assert csl["issued"] == {"date-parts": [[1920, 3, 15]]}

    def test_date_display_fallback(self) -> None:
        doc = _make_mock_doc(date_start=None, date_display="circa 1920")
        csl = document_to_csl_json(doc)
        assert csl["issued"] == {"literal": "circa 1920"}

    def test_url_with_base_url(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042")
        csl = document_to_csl_json(doc, base_url="https://archive.example.org")
        assert csl["URL"] == "https://archive.example.org/d/2025-0042"

    def test_no_url_without_base_url(self) -> None:
        doc = _make_mock_doc()
        csl = document_to_csl_json(doc, base_url="")
        assert "URL" not in csl

    def test_version_info_in_note(self) -> None:
        doc = _make_mock_doc(
            version_group_id=10,
            version_number=3,
            version_label="1978 Revision",
        )
        csl = document_to_csl_json(doc)
        assert csl["note"] == "1978 Revision [Version 3]"

    def test_version_info_without_label(self) -> None:
        doc = _make_mock_doc(version_group_id=10, version_number=2, version_label=None)
        csl = document_to_csl_json(doc)
        assert csl["note"] == "Version 2"

    def test_no_version_info_when_unversioned(self) -> None:
        doc = _make_mock_doc(version_group_id=None)
        csl = document_to_csl_json(doc)
        assert "note" not in csl

    def test_abstract_from_scope(self) -> None:
        doc = _make_mock_doc(scope_and_content="A letter about land disputes.")
        csl = document_to_csl_json(doc)
        assert csl["abstract"] == "A letter about land disputes."

    def test_language(self) -> None:
        doc = _make_mock_doc(language_of_material="eng")
        csl = document_to_csl_json(doc)
        assert csl["language"] == "eng"


# ---------------------------------------------------------------------------
# Chicago note format
# ---------------------------------------------------------------------------


class TestChicagoNote:
    """Test the Chicago Manual of Style footnote/endnote citation."""

    def test_basic_citation(self) -> None:
        doc = _make_mock_doc(
            title="Falls Church VFD Bylaws",
            date_display="1920",
            accession_number="2025-0042",
        )
        citation = format_chicago_note(doc, institution_name="VFD Archives")
        assert "Falls Church VFD Bylaws" in citation
        assert "1920" in citation
        assert "Accession 2025-0042" in citation
        assert "VFD Archives" in citation
        assert citation.endswith(".")

    def test_versioned_citation(self) -> None:
        doc = _make_mock_doc(
            title="VFD Bylaws",
            version_group_id=10,
            version_number=3,
            version_label="1978 Revision",
            accession_number="2025-0042.3",
        )
        citation = format_chicago_note(doc, institution_name="VFD Archives")
        assert "1978 Revision" in citation
        assert "version 3" in citation

    def test_no_date(self) -> None:
        doc = _make_mock_doc(title="Undated Letter", date_display=None)
        citation = format_chicago_note(doc)
        assert "Undated Letter" in citation

    def test_no_accession(self) -> None:
        doc = _make_mock_doc(title="Fragment", accession_number=None)
        citation = format_chicago_note(doc, institution_name="Archives")
        assert "Accession" not in citation


# ---------------------------------------------------------------------------
# Chicago bibliography format
# ---------------------------------------------------------------------------


class TestChicagoBib:
    """Test the Chicago Manual of Style bibliography entry."""

    def test_with_creator(self) -> None:
        doc = _make_mock_doc(
            title="Letter to Mayor",
            creator="Thomas Gray",
            date_display="1920",
            accession_number="2025-0001",
        )
        bib = format_chicago_bib(doc, institution_name="VFD Archives")
        assert bib.startswith("Thomas Gray.")
        assert '"Letter to Mayor."' in bib
        assert "1920." in bib
        assert "Accession 2025-0001." in bib
        assert "VFD Archives." in bib

    def test_without_creator(self) -> None:
        doc = _make_mock_doc(title="Anonymous Pamphlet", creator=None)
        bib = format_chicago_bib(doc, institution_name="Archives")
        assert bib.startswith('"Anonymous Pamphlet."')


# ---------------------------------------------------------------------------
# Turabian
# ---------------------------------------------------------------------------


class TestTurabian:
    """Turabian format delegates to Chicago note format."""

    def test_turabian_matches_chicago_note(self) -> None:
        doc = _make_mock_doc(
            title="Deed of Trust",
            date_display="1890",
            accession_number="2025-0010",
        )
        t = format_turabian(doc, institution_name="Archives")
        c = format_chicago_note(doc, institution_name="Archives")
        assert t == c


# ---------------------------------------------------------------------------
# BibTeX
# ---------------------------------------------------------------------------


class TestBibTeX:
    """Test BibTeX entry generation."""

    def test_basic_bibtex(self) -> None:
        doc = _make_mock_doc(
            title="Survey of Falls Church",
            creator="James Morgan",
            date_start=date(1880, 1, 1),
            accession_number="2025-0005",
        )
        bib = format_bibtex(doc, institution_name="VFD Archives")
        assert bib.startswith("@misc{2025_0005,")
        assert "title = {Survey of Falls Church}" in bib
        assert "author = {James Morgan}" in bib
        assert "year = {1880}" in bib
        assert "note = {Accession 2025-0005}" in bib
        assert bib.endswith("}")

    def test_bibtex_no_creator(self) -> None:
        doc = _make_mock_doc(title="Unknown Author", creator=None)
        bib = format_bibtex(doc)
        assert "author" not in bib

    def test_bibtex_no_date(self) -> None:
        doc = _make_mock_doc(title="Undated", date_start=None)
        bib = format_bibtex(doc)
        assert "year" not in bib

    def test_bibtex_key_sanitization(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042")
        bib = format_bibtex(doc)
        # Hyphens replaced with underscores in key
        assert "@misc{2025_0042," in bib


# ---------------------------------------------------------------------------
# RIS
# ---------------------------------------------------------------------------


class TestRIS:
    """Test RIS entry generation."""

    def test_basic_ris(self) -> None:
        doc = _make_mock_doc(
            title="Council Meeting Minutes",
            creator="Mary Jones",
            date_start=date(1925, 5, 10),
            accession_number="2025-0003",
            scope_and_content="Minutes of the regular meeting.",
        )
        ris = format_ris(doc, institution_name="Falls Church Archives")
        lines = ris.split("\n")
        assert lines[0] == "TY  - GEN"
        assert "TI  - Council Meeting Minutes" in lines
        assert "AU  - Mary Jones" in lines
        assert "PY  - 1925" in lines
        assert "ID  - 2025-0003" in lines
        assert "PB  - Falls Church Archives" in lines
        assert any(line.startswith("AB  -") for line in lines)
        assert lines[-1] == "ER  -"

    def test_ris_no_creator(self) -> None:
        doc = _make_mock_doc(creator=None)
        ris = format_ris(doc)
        assert "AU" not in ris

    def test_ris_truncates_abstract(self) -> None:
        long_content = "x" * 1000
        doc = _make_mock_doc(scope_and_content=long_content)
        ris = format_ris(doc)
        ab_line = [l for l in ris.split("\n") if l.startswith("AB  -")][0]
        # Abstract is truncated to 500 chars
        assert len(ab_line.replace("AB  - ", "")) <= 500

    def test_ris_no_abstract_when_no_scope(self) -> None:
        doc = _make_mock_doc(scope_and_content=None)
        ris = format_ris(doc)
        assert "AB  -" not in ris


# ---------------------------------------------------------------------------
# Versioned documents across all formats
# ---------------------------------------------------------------------------


class TestVersionedCitations:
    """Verify that versioned accession numbers appear correctly in all formats."""

    def test_versioned_accession_in_chicago_note(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042.3")
        citation = format_chicago_note(doc)
        assert "2025-0042.3" in citation

    def test_versioned_accession_in_bibtex(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042.3")
        bib = format_bibtex(doc)
        assert "Accession 2025-0042.3" in bib

    def test_versioned_accession_in_ris(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042.3")
        ris = format_ris(doc)
        assert "ID  - 2025-0042.3" in ris

    def test_versioned_accession_in_csl_json(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042.3")
        csl = document_to_csl_json(doc)
        assert csl["id"] == "2025-0042.3"
        assert csl["call-number"] == "2025-0042.3"
