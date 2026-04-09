"""Unit tests for StorageResolver — path sanitization, path computation for all
five storage schemes, quarantine/thumbnail/export directory helpers."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.storage.resolver import StorageResolver


# ---------------------------------------------------------------------------
# Path component sanitization
# ---------------------------------------------------------------------------


class TestSanitizePathComponent:
    """Verify sanitize_path_component enforces the expected rules:
    lowercase, spaces to underscores, only [a-z0-9_-] allowed."""

    def test_lowercase(self) -> None:
        assert StorageResolver.sanitize_path_component("HelloWorld") == "helloworld"

    def test_spaces_to_underscores(self) -> None:
        assert StorageResolver.sanitize_path_component("my file name") == "my_file_name"

    def test_removes_special_characters(self) -> None:
        assert StorageResolver.sanitize_path_component("doc@#$%2025") == "doc2025"

    def test_preserves_hyphens(self) -> None:
        assert StorageResolver.sanitize_path_component("acc-2025") == "acc-2025"

    def test_preserves_underscores(self) -> None:
        assert StorageResolver.sanitize_path_component("my_doc") == "my_doc"

    def test_strips_whitespace(self) -> None:
        assert StorageResolver.sanitize_path_component("  padded  ") == "padded"

    def test_empty_string_returns_unknown(self) -> None:
        assert StorageResolver.sanitize_path_component("") == "unknown"

    def test_all_special_chars_returns_unknown(self) -> None:
        assert StorageResolver.sanitize_path_component("@#$%^&*()") == "unknown"

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("John Smith", "john_smith"),
            ("Falls Church VFD", "falls_church_vfd"),
            ("2025-0042", "2025-0042"),
            ("acc/2025", "acc2025"),
            ("file.pdf", "filepdf"),
        ],
    )
    def test_various_inputs(self, input_val: str, expected: str) -> None:
        assert StorageResolver.sanitize_path_component(input_val) == expected


# ---------------------------------------------------------------------------
# resolve_absolute
# ---------------------------------------------------------------------------


class TestResolveAbsolute:
    """Test converting a relative stored_path to an absolute path."""

    @patch("app.storage.resolver.settings")
    def test_resolve_absolute(self, mock_settings) -> None:
        mock_settings.STORAGE_ROOT = "/data/storage"
        result = StorageResolver.resolve_absolute("2025/01/2025-0001/letter.pdf")
        assert result == Path("/data/storage/2025/01/2025-0001/letter.pdf")

    @patch("app.storage.resolver.settings")
    def test_resolve_absolute_trailing_slash(self, mock_settings) -> None:
        mock_settings.STORAGE_ROOT = "/data/storage/"
        result = StorageResolver.resolve_absolute("files/test.jpg")
        assert result == Path("/data/storage/files/test.jpg")


# ---------------------------------------------------------------------------
# compute_path — date scheme
# ---------------------------------------------------------------------------


class TestComputePathDateScheme:
    """Test the date storage scheme: {year}/{month}/{accession}/{filename}."""

    def test_date_scheme_basic(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="date",
            accession_number="2025-0042",
            filename="letter.pdf",
            year="2025",
            month="03",
        )
        assert path == "2025/03/2025-0042/letter.pdf"

    def test_date_scheme_sanitizes_accession(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="date",
            accession_number="ACC 2025/001",
            filename="scan.tiff",
            year="2025",
            month="01",
        )
        assert "acc_2025001" in path
        assert path.endswith("/scan.tiff")

    def test_date_scheme_preserves_extension(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="date",
            accession_number="2025-0001",
            filename="document.PDF",
            year="2025",
            month="06",
        )
        assert path.endswith(".pdf")


# ---------------------------------------------------------------------------
# compute_path — location scheme
# ---------------------------------------------------------------------------


class TestComputePathLocationScheme:
    """Test the location scheme: {fonds}/{series}/{file}/{accession}/{filename}."""

    def test_location_scheme_basic(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="location",
            accession_number="2025-0001",
            filename="deed.pdf",
            fonds_id="fonds-a",
            series_id="series-1",
            file_id="file-alpha",
        )
        assert path == "fonds-a/series-1/file-alpha/2025-0001/deed.pdf"

    def test_location_scheme_sanitizes_components(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="location",
            accession_number="2025-0001",
            filename="doc.pdf",
            fonds_id="Fonds A",
            series_id="Series #1",
            file_id="File (Alpha)",
        )
        assert path.startswith("fonds_a/series_1/file_alpha/")


# ---------------------------------------------------------------------------
# compute_path — donor scheme
# ---------------------------------------------------------------------------


class TestComputePathDonorScheme:
    """Test the donor scheme: donors/{donor_slug}/{accession}/{filename}."""

    def test_donor_scheme_basic(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="donor",
            accession_number="2025-0042",
            filename="letter.jpg",
            donor_slug="smith-family",
        )
        assert path == "donors/smith-family/2025-0042/letter.jpg"

    def test_donor_scheme_sanitizes_slug(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="donor",
            accession_number="2025-0001",
            filename="photo.png",
            donor_slug="Dr. Smith & Sons",
        )
        assert "donors/dr_smith__sons/" in path or "donors/dr_smith_sons/" in path


# ---------------------------------------------------------------------------
# compute_path — subject scheme
# ---------------------------------------------------------------------------


class TestComputePathSubjectScheme:
    """Test the subject scheme: subjects/{category_slug}/{accession}/{filename}."""

    def test_subject_scheme_basic(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="subject",
            accession_number="2025-0100",
            filename="map.tiff",
            category_slug="civil-war",
        )
        assert path == "subjects/civil-war/2025-0100/map.tiff"

    def test_subject_scheme_sanitizes_category(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="subject",
            accession_number="2025-0001",
            filename="report.pdf",
            category_slug="Local History & Heritage",
        )
        assert path.startswith("subjects/local_history__heritage/") or \
               path.startswith("subjects/local_history_heritage/")


# ---------------------------------------------------------------------------
# compute_path — record_number scheme
# ---------------------------------------------------------------------------


class TestComputePathRecordNumberScheme:
    """Test the record_number scheme: records/{prefix}/{accession}/{filename}."""

    def test_record_number_scheme_basic(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="record_number",
            accession_number="2025-0001",
            filename="invoice.pdf",
            record_number_prefix="REC-A",
        )
        assert path == "records/rec-a/2025-0001/invoice.pdf"


# ---------------------------------------------------------------------------
# compute_path — unknown scheme (fallback)
# ---------------------------------------------------------------------------


class TestComputePathUnknownScheme:
    """An unknown scheme type falls back to files/{accession}/{filename}."""

    def test_unknown_scheme_fallback(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="chronological",
            accession_number="2025-0001",
            filename="doc.pdf",
        )
        assert path == "files/2025-0001/doc.pdf"

    def test_empty_scheme_fallback(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="",
            accession_number="2025-0001",
            filename="doc.pdf",
        )
        assert path.startswith("files/")


# ---------------------------------------------------------------------------
# Quarantine, thumbnail, export directory helpers
# ---------------------------------------------------------------------------


class TestDirectoryHelpers:
    """Test quarantine, thumbnail, and export directory creation helpers."""

    @patch("app.storage.resolver.settings")
    def test_quarantine_path(self, mock_settings) -> None:
        mock_settings.STORAGE_ROOT = "/tmp/test_storage"
        path = StorageResolver.quarantine_path("uuid-123", "letter.pdf")
        assert path == Path("/tmp/test_storage/.quarantine/uuid-123_letter.pdf")

    @patch("app.storage.resolver.settings")
    def test_thumbnail_dir(self, mock_settings) -> None:
        mock_settings.STORAGE_ROOT = "/tmp/test_storage"
        tdir = StorageResolver.thumbnail_dir(42)
        assert tdir == Path("/tmp/test_storage/.thumbnails/42")

    @patch("app.storage.resolver.settings")
    def test_export_dir(self, mock_settings) -> None:
        mock_settings.STORAGE_ROOT = "/tmp/test_storage"
        edir = StorageResolver.export_dir("export-uuid-456")
        assert edir == Path("/tmp/test_storage/.exports/export-uuid-456")


# ---------------------------------------------------------------------------
# Extension handling
# ---------------------------------------------------------------------------


class TestExtensionHandling:
    """Verify that file extensions are lowercased and preserved correctly."""

    @pytest.mark.parametrize(
        "filename,expected_ext",
        [
            ("photo.JPEG", ".jpeg"),
            ("scan.TIFF", ".tiff"),
            ("doc.PDF", ".pdf"),
            ("image.png", ".png"),
            ("archive.tar.gz", ".gz"),
        ],
    )
    def test_extensions_lowercased(self, filename: str, expected_ext: str) -> None:
        path = StorageResolver.compute_path(
            scheme_type="date",
            accession_number="2025-0001",
            filename=filename,
            year="2025",
            month="01",
        )
        assert path.endswith(expected_ext)

    def test_filename_without_extension(self) -> None:
        path = StorageResolver.compute_path(
            scheme_type="date",
            accession_number="2025-0001",
            filename="noextension",
            year="2025",
            month="01",
        )
        # The stem is sanitized and there's no extension to append
        assert "/" in path
