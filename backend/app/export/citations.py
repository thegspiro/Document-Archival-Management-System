"""Citation export formatters.

Supports Chicago (note and bibliography), Turabian, BibTeX, RIS, CSL-JSON,
and Zotero RDF. Uses CSL-JSON as the intermediate representation.
"""

from typing import Any

from app.models.document import Document


def document_to_csl_json(
    document: Document,
    institution_name: str = "",
    base_url: str = "",
) -> dict[str, Any]:
    """Convert a Document to CSL-JSON format."""
    csl: dict[str, Any] = {
        "id": document.accession_number or str(document.id),
        "type": "manuscript",
        "title": document.title,
        "archive": institution_name,
        "archive_location": document.original_location or "",
        "call-number": document.accession_number or "",
    }

    if document.creator:
        csl["author"] = [{"literal": document.creator.authorized_name}]

    if document.date_start:
        csl["issued"] = {
            "date-parts": [[document.date_start.year, document.date_start.month, document.date_start.day]]
        }
    elif document.date_display:
        csl["issued"] = {"literal": document.date_display}

    if document.scope_and_content:
        csl["abstract"] = document.scope_and_content

    if document.language_of_material:
        csl["language"] = document.language_of_material

    if base_url and document.accession_number:
        csl["URL"] = f"{base_url}/d/{document.accession_number}"

    # Version information
    if document.version_group_id is not None:
        version_note = f"Version {document.version_number}"
        if document.version_label:
            version_note = f"{document.version_label} [{version_note}]"
        csl["note"] = version_note

    return csl


def format_chicago_note(
    document: Document,
    institution_name: str = "",
) -> str:
    """Format a Chicago Manual of Style footnote/endnote citation."""
    parts = []

    parts.append(document.title)

    if document.version_group_id is not None and document.version_label:
        parts.append(f"{document.version_label} [version {document.version_number}]")

    if document.date_display:
        parts.append(document.date_display)

    if document.accession_number:
        parts.append(f"Accession {document.accession_number}")

    parts.append(institution_name)

    return ", ".join(p for p in parts if p) + "."


def format_chicago_bib(
    document: Document,
    institution_name: str = "",
) -> str:
    """Format a Chicago Manual of Style bibliography entry."""
    parts = []

    if document.creator:
        parts.append(f"{document.creator.authorized_name}.")

    title = f'"{document.title}."'
    parts.append(title)

    if document.date_display:
        parts.append(f"{document.date_display}.")

    if document.accession_number:
        parts.append(f"Accession {document.accession_number}.")

    parts.append(f"{institution_name}.")

    return " ".join(p for p in parts if p)


def format_turabian(
    document: Document,
    institution_name: str = "",
) -> str:
    """Format a Turabian citation (based on Chicago)."""
    return format_chicago_note(document, institution_name)


def format_bibtex(
    document: Document,
    institution_name: str = "",
) -> str:
    """Format a BibTeX entry."""
    key = (document.accession_number or str(document.id)).replace("-", "_")
    lines = [f"@misc{{{key},"]
    lines.append(f"  title = {{{document.title}}},")

    if document.creator:
        lines.append(f"  author = {{{document.creator.authorized_name}}},")

    if document.date_start:
        lines.append(f"  year = {{{document.date_start.year}}},")

    if document.accession_number:
        lines.append(f"  note = {{Accession {document.accession_number}}},")

    lines.append(f"  howpublished = {{{institution_name}}},")
    lines.append("}")
    return "\n".join(lines)


def format_ris(
    document: Document,
    institution_name: str = "",
) -> str:
    """Format an RIS entry."""
    lines = ["TY  - GEN"]
    lines.append(f"TI  - {document.title}")

    if document.creator:
        lines.append(f"AU  - {document.creator.authorized_name}")

    if document.date_start:
        lines.append(f"PY  - {document.date_start.year}")

    if document.accession_number:
        lines.append(f"ID  - {document.accession_number}")

    lines.append(f"PB  - {institution_name}")

    if document.scope_and_content:
        lines.append(f"AB  - {document.scope_and_content[:500]}")

    lines.append("ER  -")
    return "\n".join(lines)
