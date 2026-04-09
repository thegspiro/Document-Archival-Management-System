"""Unit tests for DocumentService — CRUD, accession numbers, inbox, bulk actions."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.document_service import DocumentService


# ---------------------------------------------------------------------------
# Helper: build a mock Document
# ---------------------------------------------------------------------------


def _make_mock_doc(**overrides) -> MagicMock:
    """Return a MagicMock with default Document attributes."""
    doc = MagicMock()
    doc.id = overrides.get("id", 1)
    doc.title = overrides.get("title", "Test Document")
    doc.accession_number = overrides.get("accession_number", "2025-0001")
    doc.inbox_status = overrides.get("inbox_status", "inbox")
    doc.review_status = overrides.get("review_status", "none")
    doc.is_public = overrides.get("is_public", False)
    doc.version_group_id = overrides.get("version_group_id", None)
    doc.is_canonical_version = overrides.get("is_canonical_version", False)
    doc.arrangement_node_id = overrides.get("arrangement_node_id", None)
    doc.creator_id = overrides.get("creator_id", None)
    doc.created_by = overrides.get("created_by", None)
    doc.description_completeness = "none"
    doc.description_completeness_updated_at = None
    doc.created_at = datetime.now(tz=timezone.utc)
    doc.updated_at = datetime.now(tz=timezone.utc)
    return doc


# ---------------------------------------------------------------------------
# Accession number generation
# ---------------------------------------------------------------------------


class TestAccessionNumberGeneration:
    """Test the atomic accession number generator."""

    @pytest.mark.asyncio
    async def test_generate_accession_default_format(self) -> None:
        mock_seq = MagicMock()
        mock_seq.current_value = 41
        mock_seq.name = "accession_2026"

        seq_result = MagicMock()
        seq_result.scalar_one_or_none.return_value = mock_seq

        # System setting for format: returns None (use default)
        fmt_result = MagicMock()
        fmt_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.side_effect = [seq_result, fmt_result]

        accession = await DocumentService._generate_accession_number(db)
        # Sequence was 41, incremented to 42
        assert mock_seq.current_value == 42
        assert accession == "2026-0042"

    @pytest.mark.asyncio
    async def test_generate_accession_new_year_creates_sequence(self) -> None:
        # Sequence does not exist yet
        seq_result_none = MagicMock()
        seq_result_none.scalar_one_or_none.return_value = None

        # After insert, re-acquire with lock
        mock_seq = MagicMock()
        mock_seq.current_value = 0
        seq_result_locked = MagicMock()
        seq_result_locked.scalar_one.return_value = mock_seq

        # Format setting: None
        fmt_result = MagicMock()
        fmt_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.side_effect = [seq_result_none, seq_result_locked, fmt_result]

        accession = await DocumentService._generate_accession_number(db)
        assert mock_seq.current_value == 1
        assert accession.endswith("-0001")

    @pytest.mark.asyncio
    async def test_generate_accession_custom_format(self) -> None:
        mock_seq = MagicMock()
        mock_seq.current_value = 4

        seq_result = MagicMock()
        seq_result.scalar_one_or_none.return_value = mock_seq

        # Custom format
        fmt_result = MagicMock()
        fmt_result.scalar_one_or_none.return_value = {"format": "DOC-{YEAR}-{SEQUENCE:04d}"}

        db = AsyncMock()
        db.execute.side_effect = [seq_result, fmt_result]

        accession = await DocumentService._generate_accession_number(db)
        assert mock_seq.current_value == 5
        assert accession.startswith("DOC-")
        assert accession.endswith("-0005")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class TestCreateDocument:
    """Test document creation with auto-accession and audit logging."""

    @pytest.mark.asyncio
    @patch.object(DocumentService, "_generate_accession_number", return_value="2026-0099")
    async def test_create_auto_accession(self, mock_gen: AsyncMock) -> None:
        db = AsyncMock()

        doc = await DocumentService.create_document(
            db,
            data={"title": "New Letter"},
            created_by=3,
            ip_address="127.0.0.1",
        )

        # Accession was auto-generated
        mock_gen.assert_called_once()
        db.add.assert_called_once()
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(DocumentService, "_generate_accession_number")
    async def test_create_with_explicit_accession(self, mock_gen: AsyncMock) -> None:
        db = AsyncMock()

        await DocumentService.create_document(
            db,
            data={"title": "Deed", "accession_number": "CUSTOM-001"},
            created_by=1,
        )

        # Should NOT generate an accession number
        mock_gen.assert_not_called()

    @pytest.mark.asyncio
    @patch.object(DocumentService, "_generate_accession_number", return_value="2026-0001")
    async def test_create_sets_created_by(self, _: AsyncMock) -> None:
        db = AsyncMock()

        await DocumentService.create_document(
            db,
            data={"title": "Map"},
            created_by=42,
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.created_by == 42


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class TestGetDocument:
    """Test single document retrieval."""

    @pytest.mark.asyncio
    async def test_get_document_found(self) -> None:
        mock_doc = _make_mock_doc(id=7)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc

        db = AsyncMock()
        db.execute.return_value = mock_result

        doc = await DocumentService.get_document(db, document_id=7)
        assert doc.id == 7

    @pytest.mark.asyncio
    async def test_get_document_not_found(self) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.get_document(db, document_id=999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# List with pagination
# ---------------------------------------------------------------------------


class TestListDocuments:
    """Test paginated document listing with filters."""

    @pytest.mark.asyncio
    async def test_list_default_pagination(self) -> None:
        mock_docs = [_make_mock_doc(id=i) for i in range(3)]

        count_result = MagicMock()
        count_result.scalar_one.return_value = 3

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = mock_docs

        db = AsyncMock()
        db.execute.side_effect = [count_result, items_result]

        result = await DocumentService.list_documents(db, page=1, per_page=25)
        assert result["total"] == 3
        assert result["page"] == 1
        assert result["per_page"] == 25
        assert len(result["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_with_inbox_filter(self) -> None:
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [_make_mock_doc()]

        db = AsyncMock()
        db.execute.side_effect = [count_result, items_result]

        result = await DocumentService.list_documents(db, inbox_status="inbox")
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_list_pages_calculation(self) -> None:
        count_result = MagicMock()
        count_result.scalar_one.return_value = 51

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []

        db = AsyncMock()
        db.execute.side_effect = [count_result, items_result]

        result = await DocumentService.list_documents(db, page=1, per_page=25)
        assert result["pages"] == 3  # ceil(51/25) = 3

    @pytest.mark.asyncio
    async def test_list_empty_result(self) -> None:
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []

        db = AsyncMock()
        db.execute.side_effect = [count_result, items_result]

        result = await DocumentService.list_documents(db)
        assert result["total"] == 0
        assert result["items"] == []
        assert result["pages"] == 0


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------


class TestInboxDocuments:
    """Test inbox retrieval delegates to list_documents with inbox filter."""

    @pytest.mark.asyncio
    @patch.object(DocumentService, "list_documents")
    async def test_get_inbox_delegates(self, mock_list: AsyncMock) -> None:
        mock_list.return_value = {"items": [], "total": 0, "page": 1, "per_page": 25, "pages": 0}
        db = AsyncMock()

        await DocumentService.get_inbox_documents(db, user_id=1)
        mock_list.assert_called_once_with(
            db, page=1, per_page=25, inbox_status="inbox"
        )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class TestUpdateDocument:
    """Test document updates with protected fields and audit logging."""

    @pytest.mark.asyncio
    @patch.object(DocumentService, "get_document")
    async def test_update_applies_changes(self, mock_get: AsyncMock) -> None:
        mock_doc = _make_mock_doc(title="Old Title")
        mock_get.return_value = mock_doc
        db = AsyncMock()

        result = await DocumentService.update_document(
            db,
            document_id=1,
            data={"title": "New Title"},
            acting_user_id=5,
        )
        assert mock_doc.title == "New Title"

    @pytest.mark.asyncio
    @patch.object(DocumentService, "get_document")
    async def test_update_protects_id(self, mock_get: AsyncMock) -> None:
        mock_doc = _make_mock_doc(id=1)
        mock_get.return_value = mock_doc
        db = AsyncMock()

        await DocumentService.update_document(
            db,
            document_id=1,
            data={"id": 999},
            acting_user_id=5,
        )
        # The protected field should not be changed
        assert mock_doc.id == 1

    @pytest.mark.asyncio
    @patch.object(DocumentService, "get_document")
    async def test_update_protects_completeness_fields(self, mock_get: AsyncMock) -> None:
        mock_doc = _make_mock_doc()
        mock_doc.description_completeness = "minimal"
        mock_get.return_value = mock_doc
        db = AsyncMock()

        await DocumentService.update_document(
            db,
            document_id=1,
            data={"description_completeness": "full"},
            acting_user_id=5,
        )
        assert mock_doc.description_completeness == "minimal"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


class TestDeleteDocument:
    """Test document deletion with audit logging."""

    @pytest.mark.asyncio
    @patch.object(DocumentService, "get_document")
    async def test_delete_success(self, mock_get: AsyncMock) -> None:
        mock_doc = _make_mock_doc(id=10)
        mock_get.return_value = mock_doc
        db = AsyncMock()

        await DocumentService.delete_document(
            db, document_id=10, acting_user_id=1, ip_address="10.0.0.1"
        )
        db.delete.assert_called_once_with(mock_doc)
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(DocumentService, "get_document")
    async def test_delete_not_found(self, mock_get: AsyncMock) -> None:
        mock_get.side_effect = HTTPException(status_code=404, detail="Document not found")
        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.delete_document(db, document_id=999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Bulk actions
# ---------------------------------------------------------------------------


class TestBulkAction:
    """Test bulk operations on multiple documents."""

    @pytest.mark.asyncio
    async def test_bulk_apply_terms_requires_term_ids(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1, 2],
                action_type="apply_terms",
                term_ids=None,
            )
        assert exc_info.value.status_code == 400
        assert "term_ids required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bulk_remove_terms_requires_term_ids(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1],
                action_type="remove_terms",
                term_ids=None,
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_bulk_assign_node_requires_node_id(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1, 2, 3],
                action_type="assign_node",
                node_id=None,
            )
        assert exc_info.value.status_code == 400
        assert "node_id required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bulk_set_public_requires_is_public(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1],
                action_type="set_public",
                is_public=None,
            )
        assert exc_info.value.status_code == 400
        assert "is_public required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bulk_delete_requires_reason(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1],
                action_type="delete",
                reason=None,
            )
        assert exc_info.value.status_code == 400
        assert "reason required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bulk_unknown_action_type(self) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await DocumentService.bulk_action(
                db,
                document_ids=[1],
                action_type="nonexistent_action",
            )
        assert exc_info.value.status_code == 400
        assert "Unknown bulk action" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bulk_clear_inbox(self) -> None:
        db = AsyncMock()
        affected = await DocumentService.bulk_action(
            db,
            document_ids=[1, 2, 3],
            action_type="clear_inbox",
        )
        assert affected == 3
        db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_bulk_set_public(self) -> None:
        db = AsyncMock()
        affected = await DocumentService.bulk_action(
            db,
            document_ids=[1, 2],
            action_type="set_public",
            is_public=True,
        )
        assert affected == 2

    @pytest.mark.asyncio
    async def test_bulk_assign_node(self) -> None:
        db = AsyncMock()
        affected = await DocumentService.bulk_action(
            db,
            document_ids=[5, 6, 7, 8],
            action_type="assign_node",
            node_id=10,
        )
        assert affected == 4
