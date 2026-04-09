"""Unit tests for VocabularyService — domain/term CRUD, term merging with
audit log, deduplication during merge."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.vocabulary_service import VocabularyService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_domain(**overrides) -> MagicMock:
    dom = MagicMock()
    dom.id = overrides.get("id", 1)
    dom.name = overrides.get("name", "tag")
    dom.description = overrides.get("description", None)
    dom.allows_user_addition = overrides.get("allows_user_addition", True)
    return dom


def _make_mock_term(**overrides) -> MagicMock:
    term = MagicMock()
    term.id = overrides.get("id", 1)
    term.domain_id = overrides.get("domain_id", 1)
    term.term = overrides.get("term", "letter")
    term.definition = overrides.get("definition", None)
    term.broader_term_id = overrides.get("broader_term_id", None)
    term.is_active = overrides.get("is_active", True)
    term.sort_order = overrides.get("sort_order", 0)
    term.created_by = overrides.get("created_by", None)
    return term


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------


class TestCreateDomain:
    """Test vocabulary domain creation."""

    @pytest.mark.asyncio
    async def test_create_domain_success(self) -> None:
        # No existing domain with the same name
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = existing_result

        domain = await VocabularyService.create_domain(
            db, name="document_type", description="Types of documents"
        )
        db.add.assert_called_once()
        db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_create_domain_duplicate_raises_409(self) -> None:
        existing = _make_mock_domain(name="tag")
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = existing

        db = AsyncMock()
        db.execute.return_value = existing_result

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.create_domain(db, name="tag")
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail


class TestGetDomain:
    """Test domain retrieval."""

    @pytest.mark.asyncio
    async def test_get_domain_found(self) -> None:
        domain = _make_mock_domain(id=3)
        result = MagicMock()
        result.scalar_one_or_none.return_value = domain

        db = AsyncMock()
        db.execute.return_value = result

        d = await VocabularyService.get_domain(db, domain_id=3)
        assert d.id == 3

    @pytest.mark.asyncio
    async def test_get_domain_not_found(self) -> None:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.get_domain(db, domain_id=999)
        assert exc_info.value.status_code == 404


class TestListDomains:
    """Test listing all domains."""

    @pytest.mark.asyncio
    async def test_list_domains(self) -> None:
        domains = [_make_mock_domain(id=i) for i in range(3)]
        result = MagicMock()
        result.scalars.return_value.all.return_value = domains

        db = AsyncMock()
        db.execute.return_value = result

        found = await VocabularyService.list_domains(db)
        assert len(found) == 3


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------


class TestCreateTerm:
    """Test vocabulary term creation."""

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_domain")
    async def test_create_term_success(self, mock_get_domain: AsyncMock) -> None:
        mock_get_domain.return_value = _make_mock_domain(id=1)

        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = existing_result

        term = await VocabularyService.create_term(
            db, domain_id=1, term="photograph", definition="A photographic image"
        )
        db.add.assert_called_once()
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_domain")
    async def test_create_term_duplicate_raises_409(self, mock_get_domain: AsyncMock) -> None:
        mock_get_domain.return_value = _make_mock_domain(id=1)

        existing = _make_mock_term(domain_id=1, term="letter")
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = existing

        db = AsyncMock()
        db.execute.return_value = existing_result

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.create_term(db, domain_id=1, term="letter")
        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_domain")
    async def test_create_term_nonexistent_domain(self, mock_get_domain: AsyncMock) -> None:
        mock_get_domain.side_effect = HTTPException(status_code=404, detail="Vocabulary domain not found")

        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.create_term(db, domain_id=999, term="test")
        assert exc_info.value.status_code == 404


class TestGetTerm:
    """Test term retrieval."""

    @pytest.mark.asyncio
    async def test_get_term_found(self) -> None:
        term = _make_mock_term(id=7)
        result = MagicMock()
        result.scalar_one_or_none.return_value = term

        db = AsyncMock()
        db.execute.return_value = result

        t = await VocabularyService.get_term(db, term_id=7)
        assert t.id == 7

    @pytest.mark.asyncio
    async def test_get_term_not_found(self) -> None:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = result

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.get_term(db, term_id=999)
        assert exc_info.value.status_code == 404


class TestUpdateTerm:
    """Test term update with protected fields."""

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_update_term_renames(self, mock_get: AsyncMock) -> None:
        term = _make_mock_term(id=5, term="leter")
        mock_get.return_value = term
        db = AsyncMock()

        result = await VocabularyService.update_term(
            db, term_id=5, data={"term": "letter"}
        )
        assert term.term == "letter"
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_update_term_protects_domain_id(self, mock_get: AsyncMock) -> None:
        term = _make_mock_term(id=5, domain_id=1)
        mock_get.return_value = term
        db = AsyncMock()

        await VocabularyService.update_term(
            db, term_id=5, data={"domain_id": 99}
        )
        # domain_id should not change (protected)
        assert term.domain_id == 1

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_update_term_deactivate(self, mock_get: AsyncMock) -> None:
        term = _make_mock_term(id=5, is_active=True)
        mock_get.return_value = term
        db = AsyncMock()

        await VocabularyService.update_term(
            db, term_id=5, data={"is_active": False}
        )
        assert term.is_active is False


class TestDeleteTerm:
    """Test soft-delete of vocabulary terms."""

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_delete_term_sets_inactive(self, mock_get: AsyncMock) -> None:
        term = _make_mock_term(id=5, is_active=True)
        mock_get.return_value = term
        db = AsyncMock()

        await VocabularyService.delete_term(db, term_id=5)
        assert term.is_active is False
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_delete_nonexistent_term(self, mock_get: AsyncMock) -> None:
        mock_get.side_effect = HTTPException(status_code=404, detail="Vocabulary term not found")
        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.delete_term(db, term_id=999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Term merging
# ---------------------------------------------------------------------------


class TestMergeTerm:
    """Test the term merge workflow: reassign document_terms, delete source, audit log."""

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_merge_same_term_raises_400(self, mock_get: AsyncMock) -> None:
        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.merge_term(
                db, source_term_id=5, target_term_id=5
            )
        assert exc_info.value.status_code == 400
        assert "Cannot merge a term into itself" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_merge_different_domains_raises_400(self, mock_get: AsyncMock) -> None:
        source = _make_mock_term(id=1, domain_id=10, term="photo")
        target = _make_mock_term(id=2, domain_id=20, term="photograph")
        mock_get.side_effect = [source, target]

        db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await VocabularyService.merge_term(
                db, source_term_id=1, target_term_id=2
            )
        assert exc_info.value.status_code == 400
        assert "different domains" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_merge_success(self, mock_get: AsyncMock) -> None:
        source = _make_mock_term(id=1, domain_id=10, term="photo")
        target = _make_mock_term(id=2, domain_id=10, term="photograph")
        mock_get.side_effect = [source, target]

        # Count affected document_terms
        count_result = MagicMock()
        count_result.scalar_one.return_value = 5

        # Existing target doc IDs (to handle deduplication)
        target_docs_result = MagicMock()
        target_docs_result.all.return_value = [(100,), (101,)]

        db = AsyncMock()
        db.execute.side_effect = [count_result, target_docs_result, None, None]

        affected = await VocabularyService.merge_term(
            db,
            source_term_id=1,
            target_term_id=2,
            acting_user_id=3,
        )
        assert affected == 5
        db.delete.assert_called_once_with(source)
        db.flush.assert_called()

    @pytest.mark.asyncio
    @patch.object(VocabularyService, "get_term")
    async def test_merge_zero_affected(self, mock_get: AsyncMock) -> None:
        source = _make_mock_term(id=1, domain_id=10, term="typo")
        target = _make_mock_term(id=2, domain_id=10, term="correct")
        mock_get.side_effect = [source, target]

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        target_docs_result = MagicMock()
        target_docs_result.all.return_value = []

        db = AsyncMock()
        db.execute.side_effect = [count_result, target_docs_result, None]

        affected = await VocabularyService.merge_term(
            db, source_term_id=1, target_term_id=2
        )
        assert affected == 0
        db.delete.assert_called_once_with(source)


class TestListTerms:
    """Test listing terms in a domain."""

    @pytest.mark.asyncio
    async def test_list_terms_active_only(self) -> None:
        terms = [_make_mock_term(id=i) for i in range(4)]
        result = MagicMock()
        result.scalars.return_value.all.return_value = terms

        db = AsyncMock()
        db.execute.return_value = result

        found = await VocabularyService.list_terms(db, domain_id=1, active_only=True)
        assert len(found) == 4

    @pytest.mark.asyncio
    async def test_list_terms_include_inactive(self) -> None:
        terms = [_make_mock_term(id=i) for i in range(6)]
        result = MagicMock()
        result.scalars.return_value.all.return_value = terms

        db = AsyncMock()
        db.execute.return_value = result

        found = await VocabularyService.list_terms(db, domain_id=1, active_only=False)
        assert len(found) == 6
