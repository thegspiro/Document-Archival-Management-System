"""Path resolution for document file storage."""

import re
from pathlib import Path

from app.config import settings


class StorageResolver:
    """Resolves document file paths based on the active storage scheme."""

    @staticmethod
    def sanitize_path_component(value: str) -> str:
        """Sanitize a string for use as a filesystem path component."""
        value = value.lower().strip()
        value = value.replace(" ", "_")
        value = re.sub(r"[^a-z0-9_\-]", "", value)
        return value or "unknown"

    @staticmethod
    def resolve_absolute(relative_path: str) -> Path:
        """Resolve a stored relative path to an absolute path."""
        return Path(settings.STORAGE_ROOT) / relative_path

    @classmethod
    def compute_path(
        cls,
        scheme_type: str,
        accession_number: str,
        filename: str,
        *,
        year: str = "",
        month: str = "",
        fonds_id: str = "",
        series_id: str = "",
        file_id: str = "",
        donor_slug: str = "",
        category_slug: str = "",
        record_number_prefix: str = "",
    ) -> str:
        """Compute the relative storage path for a file based on the scheme."""
        safe_accession = cls.sanitize_path_component(accession_number)
        safe_filename = cls.sanitize_path_component(Path(filename).stem)
        ext = Path(filename).suffix.lower()
        safe_full = f"{safe_filename}{ext}"

        if scheme_type == "date":
            return f"{year}/{month}/{safe_accession}/{safe_full}"
        elif scheme_type == "location":
            return (
                f"{cls.sanitize_path_component(fonds_id)}/"
                f"{cls.sanitize_path_component(series_id)}/"
                f"{cls.sanitize_path_component(file_id)}/"
                f"{safe_accession}/{safe_full}"
            )
        elif scheme_type == "donor":
            return f"donors/{cls.sanitize_path_component(donor_slug)}/{safe_accession}/{safe_full}"
        elif scheme_type == "subject":
            return (
                f"subjects/{cls.sanitize_path_component(category_slug)}"
                f"/{safe_accession}/{safe_full}"
            )
        elif scheme_type == "record_number":
            return (
                f"records/{cls.sanitize_path_component(record_number_prefix)}"
                f"/{safe_accession}/{safe_full}"
            )
        else:
            return f"files/{safe_accession}/{safe_full}"

    @staticmethod
    def quarantine_path(unique_id: str, filename: str) -> Path:
        """Return the quarantine path for a file being processed."""
        qdir = Path(settings.STORAGE_ROOT) / ".quarantine"
        qdir.mkdir(parents=True, exist_ok=True)
        return qdir / f"{unique_id}_{filename}"

    @staticmethod
    def thumbnail_dir(document_file_id: int) -> Path:
        """Return the thumbnail directory for a document file."""
        tdir = Path(settings.STORAGE_ROOT) / ".thumbnails" / str(document_file_id)
        tdir.mkdir(parents=True, exist_ok=True)
        return tdir

    @staticmethod
    def export_dir(unique_id: str) -> Path:
        """Return a temporary export directory."""
        edir = Path(settings.STORAGE_ROOT) / ".exports" / unique_id
        edir.mkdir(parents=True, exist_ok=True)
        return edir
