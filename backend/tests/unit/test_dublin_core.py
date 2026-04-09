"""Unit tests for Dublin Core export — document_to_dc_dict crosswalk,
dc_xml generation, xmp_dict output, and dc_json."""

from datetime import date
from unittest.mock import MagicMock

import pytest
from lxml import etree

from app.export.dublin_core import (
    DC_NS,
    NSMAP,
    OAI_DC_NS,
    document_to_dc_dict,
    document_to_dc_json,
    document_to_dc_xml,
    document_to_xmp_dict,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_doc(**overrides) -> MagicMock:
    """Build a mock Document with Dublin Core-relevant fields."""
    doc = MagicMock()
    doc.id = overrides.get("id", 1)
    doc.title = overrides.get("title", "Test Document")
    doc.public_title = overrides.get("public_title", None)
    doc.is_public = overrides.get("is_public", False)
    doc.accession_number = overrides.get("accession_number", "2025-0042")
    doc.date_display = overrides.get("date_display", None)
    doc.date_start = overrides.get("date_start", None)
    doc.date_end = overrides.get("date_end", None)
    doc.scope_and_content = overrides.get("scope_and_content", None)
    doc.general_note = overrides.get("general_note", None)
    doc.language_of_material = overrides.get("language_of_material", None)
    doc.copyright_status = overrides.get("copyright_status", None)
    doc.rights_note = overrides.get("rights_note", None)
    doc.location_of_originals = overrides.get("location_of_originals", None)
    doc.extent = overrides.get("extent", None)
    doc.geo_location_name = overrides.get("geo_location_name", None)

    # Creator
    creator = overrides.get("creator", None)
    if creator is None:
        doc.creator = None
    else:
        mock_creator = MagicMock()
        mock_creator.authorized_name = creator
        doc.creator = mock_creator

    # Files
    files = overrides.get("files", [])
    doc.files = files

    # Terms (document_terms with term.term and term.domain.name)
    terms = overrides.get("terms", [])
    doc.terms = terms

    return doc


def _make_mock_file(mime_type: str = "application/pdf") -> MagicMock:
    f = MagicMock()
    f.mime_type = mime_type
    return f


def _make_mock_term(term_text: str, domain_name: str) -> MagicMock:
    dt = MagicMock()
    dt.term = MagicMock()
    dt.term.term = term_text
    dt.term.domain = MagicMock()
    dt.term.domain.name = domain_name
    return dt


# ---------------------------------------------------------------------------
# document_to_dc_dict (crosswalk)
# ---------------------------------------------------------------------------


class TestDocumentToDcDict:
    """Test the ADMS-to-Dublin-Core crosswalk dictionary."""

    def test_title_from_document(self) -> None:
        doc = _make_mock_doc(title="Original Title")
        dc = document_to_dc_dict(doc)
        assert dc["title"] == "Original Title"

    def test_public_title_used_when_public(self) -> None:
        doc = _make_mock_doc(
            title="Internal Title",
            public_title="Public Display Title",
            is_public=True,
        )
        dc = document_to_dc_dict(doc)
        assert dc["title"] == "Public Display Title"

    def test_public_title_not_used_when_private(self) -> None:
        doc = _make_mock_doc(
            title="Internal Title",
            public_title="Public Display Title",
            is_public=False,
        )
        dc = document_to_dc_dict(doc)
        assert dc["title"] == "Internal Title"

    def test_creator_from_authority_record(self) -> None:
        doc = _make_mock_doc(creator="John Smith")
        dc = document_to_dc_dict(doc)
        assert dc["creator"] == "John Smith"

    def test_creator_empty_when_none(self) -> None:
        doc = _make_mock_doc(creator=None)
        dc = document_to_dc_dict(doc)
        assert dc["creator"] == ""

    def test_description_from_scope_and_content(self) -> None:
        doc = _make_mock_doc(scope_and_content="A letter about town affairs.")
        dc = document_to_dc_dict(doc)
        assert dc["description"] == "A letter about town affairs."

    def test_description_falls_back_to_general_note(self) -> None:
        doc = _make_mock_doc(scope_and_content=None, general_note="Brief note")
        dc = document_to_dc_dict(doc)
        assert dc["description"] == "Brief note"

    def test_description_empty_when_both_null(self) -> None:
        doc = _make_mock_doc(scope_and_content=None, general_note=None)
        dc = document_to_dc_dict(doc)
        assert dc["description"] == ""

    def test_publisher_from_institution_name(self) -> None:
        doc = _make_mock_doc()
        dc = document_to_dc_dict(doc, institution_name="Falls Church VFD Archives")
        assert dc["publisher"] == "Falls Church VFD Archives"

    def test_date_from_date_display(self) -> None:
        doc = _make_mock_doc(date_display="January 1920")
        dc = document_to_dc_dict(doc)
        assert dc["date"] == "January 1920"

    def test_date_created_from_date_start(self) -> None:
        doc = _make_mock_doc(date_start=date(1920, 3, 15))
        dc = document_to_dc_dict(doc)
        assert dc["date_created"] == "1920-03-15"

    def test_identifier_with_base_url(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042")
        dc = document_to_dc_dict(doc, base_url="https://archive.example.org")
        assert dc["identifier"] == "2025-0042"
        assert dc["identifier_uri"] == "https://archive.example.org/d/2025-0042"

    def test_identifier_without_base_url(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042")
        dc = document_to_dc_dict(doc, base_url="")
        assert "identifier_uri" not in dc

    def test_language(self) -> None:
        doc = _make_mock_doc(language_of_material="eng")
        dc = document_to_dc_dict(doc)
        assert dc["language"] == "eng"

    def test_rights_combined(self) -> None:
        doc = _make_mock_doc(
            copyright_status="public_domain",
            rights_note="No known restrictions",
        )
        dc = document_to_dc_dict(doc)
        assert "public_domain" in dc["rights"]
        assert "No known restrictions" in dc["rights"]

    def test_rights_empty_when_none(self) -> None:
        doc = _make_mock_doc(copyright_status=None, rights_note=None)
        dc = document_to_dc_dict(doc)
        assert dc["rights"] == ""

    def test_source_from_location_of_originals(self) -> None:
        doc = _make_mock_doc(location_of_originals="Original at county courthouse")
        dc = document_to_dc_dict(doc)
        assert dc["source"] == "Original at county courthouse"

    def test_format_from_first_file(self) -> None:
        mock_file = _make_mock_file("image/tiff")
        doc = _make_mock_doc(files=[mock_file])
        dc = document_to_dc_dict(doc)
        assert dc["format"] == "image/tiff"

    def test_format_empty_when_no_files(self) -> None:
        doc = _make_mock_doc(files=[])
        dc = document_to_dc_dict(doc)
        assert dc["format"] == ""

    def test_extent(self) -> None:
        doc = _make_mock_doc(extent="3 pages")
        dc = document_to_dc_dict(doc)
        assert dc["extent"] == "3 pages"

    def test_spatial_from_geo_location_name(self) -> None:
        doc = _make_mock_doc(geo_location_name="Falls Church, VA")
        dc = document_to_dc_dict(doc)
        assert dc["spatial"] == "Falls Church, VA"

    def test_temporal_with_date_range(self) -> None:
        doc = _make_mock_doc(
            date_start=date(1920, 1, 1),
            date_end=date(1925, 12, 31),
        )
        dc = document_to_dc_dict(doc)
        assert dc["temporal"] == "1920-01-01/1925-12-31"

    def test_temporal_with_single_date(self) -> None:
        doc = _make_mock_doc(date_start=date(1920, 3, 15), date_end=None)
        dc = document_to_dc_dict(doc)
        assert dc["temporal"] == "1920-03-15"

    def test_temporal_empty_when_no_dates(self) -> None:
        doc = _make_mock_doc(date_start=None, date_end=None)
        dc = document_to_dc_dict(doc)
        assert dc["temporal"] == ""

    def test_subject_from_tag_terms(self) -> None:
        tag1 = _make_mock_term("fire department", "tag")
        tag2 = _make_mock_term("local government", "subject_category")
        non_tag = _make_mock_term("letter", "document_type")
        doc = _make_mock_doc(terms=[tag1, tag2, non_tag])
        dc = document_to_dc_dict(doc)
        assert "fire department" in dc["subject"]
        assert "local government" in dc["subject"]
        assert "letter" not in dc["subject"]

    def test_subject_empty_when_no_terms(self) -> None:
        doc = _make_mock_doc(terms=[])
        dc = document_to_dc_dict(doc)
        assert dc["subject"] == []


# ---------------------------------------------------------------------------
# document_to_xmp_dict
# ---------------------------------------------------------------------------


class TestDocumentToXmpDict:
    """Test the XMP dictionary used for pikepdf/Pillow embedding."""

    def test_xmp_dict_keys(self) -> None:
        doc = _make_mock_doc(
            title="XMP Test",
            creator="Jane Doe",
            scope_and_content="Description text",
        )
        xmp = document_to_xmp_dict(doc)
        required_keys = {
            "title", "creator", "description", "date", "identifier",
            "subject", "rights", "language", "publisher",
        }
        assert required_keys.issubset(set(xmp.keys()))

    def test_xmp_dict_values(self) -> None:
        doc = _make_mock_doc(
            title="XMP Values Test",
            accession_number="2025-0099",
            date_display="1890",
        )
        xmp = document_to_xmp_dict(doc)
        assert xmp["title"] == "XMP Values Test"
        assert xmp["identifier"] == "2025-0099"
        assert xmp["date"] == "1890"


# ---------------------------------------------------------------------------
# document_to_dc_xml
# ---------------------------------------------------------------------------


class TestDocumentToDcXml:
    """Test Dublin Core XML generation using lxml."""

    def test_xml_is_valid(self) -> None:
        doc = _make_mock_doc(title="XML Test", creator="Author")
        xml_bytes = document_to_dc_xml(doc, institution_name="Archives")
        # Should parse without errors
        root = etree.fromstring(xml_bytes)
        assert root is not None

    def test_xml_root_element(self) -> None:
        doc = _make_mock_doc(title="Root Test")
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        assert root.tag == f"{{{OAI_DC_NS}}}dc"

    def test_xml_contains_title(self) -> None:
        doc = _make_mock_doc(title="Survey Map of Falls Church")
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        title_el = root.find(f"{{{DC_NS}}}title")
        assert title_el is not None
        assert title_el.text == "Survey Map of Falls Church"

    def test_xml_contains_creator(self) -> None:
        doc = _make_mock_doc(creator="Thomas Gray")
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        creator_el = root.find(f"{{{DC_NS}}}creator")
        assert creator_el is not None
        assert creator_el.text == "Thomas Gray"

    def test_xml_omits_empty_fields(self) -> None:
        doc = _make_mock_doc(
            creator=None,
            scope_and_content=None,
            general_note=None,
            language_of_material=None,
        )
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        # Creator is empty string, so element should be absent
        creator_el = root.find(f"{{{DC_NS}}}creator")
        assert creator_el is None
        desc_el = root.find(f"{{{DC_NS}}}description")
        assert desc_el is None

    def test_xml_multiple_subjects(self) -> None:
        tag1 = _make_mock_term("fire department", "tag")
        tag2 = _make_mock_term("history", "tag")
        doc = _make_mock_doc(terms=[tag1, tag2])
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        subjects = root.findall(f"{{{DC_NS}}}subject")
        assert len(subjects) == 2
        texts = {s.text for s in subjects}
        assert "fire department" in texts
        assert "history" in texts

    def test_xml_declaration(self) -> None:
        doc = _make_mock_doc(title="Decl Test")
        xml_bytes = document_to_dc_xml(doc)
        xml_str = xml_bytes.decode("utf-8")
        assert xml_str.startswith("<?xml version=")
        assert 'encoding="UTF-8"' in xml_str.split("\n")[0]

    def test_xml_schema_location(self) -> None:
        doc = _make_mock_doc(title="Schema Test")
        xml_bytes = document_to_dc_xml(doc)
        xml_str = xml_bytes.decode("utf-8")
        assert "schemaLocation" in xml_str
        assert "oai_dc.xsd" in xml_str

    def test_xml_contains_publisher(self) -> None:
        doc = _make_mock_doc()
        xml_bytes = document_to_dc_xml(doc, institution_name="Falls Church Archives")
        root = etree.fromstring(xml_bytes)
        pub_el = root.find(f"{{{DC_NS}}}publisher")
        assert pub_el is not None
        assert pub_el.text == "Falls Church Archives"

    def test_xml_contains_identifier(self) -> None:
        doc = _make_mock_doc(accession_number="2025-0042")
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        id_el = root.find(f"{{{DC_NS}}}identifier")
        assert id_el is not None
        assert id_el.text == "2025-0042"

    def test_xml_contains_rights(self) -> None:
        doc = _make_mock_doc(
            copyright_status="public_domain",
            rights_note="No restrictions",
        )
        xml_bytes = document_to_dc_xml(doc)
        root = etree.fromstring(xml_bytes)
        rights_el = root.find(f"{{{DC_NS}}}rights")
        assert rights_el is not None
        assert "public_domain" in rights_el.text


# ---------------------------------------------------------------------------
# document_to_dc_json
# ---------------------------------------------------------------------------


class TestDocumentToDcJson:
    """Test the JSON variant of the Dublin Core export."""

    def test_dc_json_matches_dc_dict(self) -> None:
        doc = _make_mock_doc(title="JSON Test", creator="Author")
        dc_dict = document_to_dc_dict(doc, institution_name="Arch")
        dc_json = document_to_dc_json(doc, institution_name="Arch")
        assert dc_dict == dc_json

    def test_dc_json_has_all_keys(self) -> None:
        doc = _make_mock_doc(title="Keys Test")
        dc = document_to_dc_json(doc)
        expected_keys = {
            "title", "creator", "description", "publisher", "date",
            "identifier", "language", "rights", "source", "format",
            "extent", "spatial", "temporal", "subject", "type",
        }
        assert expected_keys.issubset(set(dc.keys()))


# ---------------------------------------------------------------------------
# Namespace constants
# ---------------------------------------------------------------------------


class TestNamespaceConstants:
    """Verify the namespace constants are correct for oai_dc."""

    def test_oai_dc_namespace(self) -> None:
        assert OAI_DC_NS == "http://www.openarchives.org/OAI/2.0/oai_dc/"

    def test_dc_namespace(self) -> None:
        assert DC_NS == "http://purl.org/dc/elements/1.1/"

    def test_nsmap_keys(self) -> None:
        assert "oai_dc" in NSMAP
        assert "dc" in NSMAP
        assert "dcterms" in NSMAP
        assert "xsi" in NSMAP
