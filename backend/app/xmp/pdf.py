"""XMP Dublin Core embedding for PDF files using pikepdf."""

from pathlib import Path

import pikepdf


def embed_dc_xmp(input_path: Path, dc: dict, output_path: Path) -> None:
    """Write Dublin Core XMP metadata into a PDF without modifying the original."""
    with pikepdf.open(input_path) as pdf:
        with pdf.open_metadata() as meta:
            if dc.get("title"):
                meta["dc:title"] = dc["title"]
            if dc.get("creator"):
                creators = dc["creator"]
                if isinstance(creators, str):
                    creators = [creators]
                meta["dc:creator"] = creators
            if dc.get("description"):
                meta["dc:description"] = dc["description"]
            if dc.get("date"):
                meta["dc:date"] = dc["date"]
            if dc.get("identifier"):
                meta["dc:identifier"] = dc["identifier"]
            if dc.get("subject"):
                subjects = dc["subject"]
                if isinstance(subjects, str):
                    subjects = [subjects]
                meta["dc:subject"] = subjects
            if dc.get("rights"):
                meta["dc:rights"] = dc["rights"]
            if dc.get("language"):
                meta["dc:language"] = dc["language"]
            if dc.get("publisher"):
                meta["dc:publisher"] = dc["publisher"]
            meta["dc:format"] = "application/pdf"
        pdf.save(output_path)
