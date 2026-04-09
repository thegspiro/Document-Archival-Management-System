"""Dublin Core export — XML, JSON, and XMP dictionary formats.

Implements the crosswalk defined in CLAUDE.md section 22.
"""

from typing import Any

from lxml import etree

from app.models.document import Document

# Namespaces
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    "oai_dc": OAI_DC_NS,
    "dc": DC_NS,
    "dcterms": DCTERMS_NS,
    "xsi": XSI_NS,
}


def document_to_dc_dict(
    document: Document,
    institution_name: str = "",
    base_url: str = "",
) -> dict[str, Any]:
    """Convert a Document to a Dublin Core dictionary."""
    dc: dict[str, Any] = {}

    # dc:title
    dc["title"] = (
        document.public_title
        if document.is_public and document.public_title
        else document.title
    )

    # dc:creator
    if document.creator:
        dc["creator"] = document.creator.authorized_name
    else:
        dc["creator"] = ""

    # dc:description
    dc["description"] = document.scope_and_content or document.general_note or ""

    # dc:publisher
    dc["publisher"] = institution_name

    # dc:date
    dc["date"] = document.date_display or ""
    if document.date_start:
        dc["date_created"] = str(document.date_start)

    # dc:identifier
    identifier = document.accession_number or ""
    if base_url and identifier:
        dc["identifier_uri"] = f"{base_url}/d/{identifier}"
    dc["identifier"] = identifier

    # dc:language
    dc["language"] = document.language_of_material or ""

    # dc:rights
    rights_parts = []
    if document.copyright_status:
        rights_parts.append(document.copyright_status)
    if document.rights_note:
        rights_parts.append(document.rights_note)
    dc["rights"] = "; ".join(rights_parts)

    # dc:source
    dc["source"] = document.location_of_originals or ""

    # dc:format
    if document.files:
        dc["format"] = document.files[0].mime_type or ""
    else:
        dc["format"] = ""

    # dc:format (extent)
    dc["extent"] = document.extent or ""

    # dc:coverage (spatial)
    dc["spatial"] = document.geo_location_name or ""

    # dc:coverage (temporal)
    if document.date_start and document.date_end:
        dc["temporal"] = f"{document.date_start}/{document.date_end}"
    elif document.date_start:
        dc["temporal"] = str(document.date_start)
    else:
        dc["temporal"] = ""

    # dc:subject — from terms
    dc["subject"] = [
        dt.term.term for dt in (document.terms or [])
        if dt.term and dt.term.domain and dt.term.domain.name in ("tag", "subject_category")
    ]

    # dc:type
    dc["type"] = ""

    return dc


def document_to_xmp_dict(document: Document) -> dict[str, Any]:
    """Convert a Document to the dict format expected by xmp/pdf.py."""
    dc = document_to_dc_dict(document)
    return {
        "title": dc.get("title", ""),
        "creator": dc.get("creator", ""),
        "description": dc.get("description", ""),
        "date": dc.get("date", ""),
        "identifier": dc.get("identifier", ""),
        "subject": dc.get("subject", []),
        "rights": dc.get("rights", ""),
        "language": dc.get("language", ""),
        "publisher": dc.get("publisher", ""),
    }


def document_to_dc_xml(
    document: Document,
    institution_name: str = "",
    base_url: str = "",
) -> bytes:
    """Generate Dublin Core oai_dc XML for a document."""
    dc = document_to_dc_dict(document, institution_name, base_url)

    root = etree.Element(
        f"{{{OAI_DC_NS}}}dc",
        nsmap=NSMAP,
    )
    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{OAI_DC_NS} http://www.openarchives.org/OAI/2.0/oai_dc.xsd",
    )

    def add_element(tag: str, text: str) -> None:
        if text:
            el = etree.SubElement(root, f"{{{DC_NS}}}{tag}")
            el.text = text

    add_element("title", dc.get("title", ""))
    add_element("creator", dc.get("creator", ""))
    for subj in dc.get("subject", []):
        add_element("subject", subj)
    add_element("description", dc.get("description", ""))
    add_element("publisher", dc.get("publisher", ""))
    add_element("date", dc.get("date", ""))
    add_element("type", dc.get("type", ""))
    add_element("format", dc.get("format", ""))
    add_element("identifier", dc.get("identifier", ""))
    add_element("source", dc.get("source", ""))
    add_element("language", dc.get("language", ""))
    add_element("rights", dc.get("rights", ""))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def document_to_dc_json(
    document: Document,
    institution_name: str = "",
    base_url: str = "",
) -> dict[str, Any]:
    """Generate Dublin Core JSON for API consumers."""
    return document_to_dc_dict(document, institution_name, base_url)
