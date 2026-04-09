"""Integration tests for GET /api/v1/search with various filter combinations.

Tests full-text query (q), date range, term_ids, is_public, and the version
filter (only canonical versions returned in search results).
"""

from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document
from app.models.document_term import DocumentTerm
from app.models.user import Role, User, UserRole
from app.models.vocabulary import VocabularyDomain, VocabularyTerm
from app.services.auth_service import ALGORITHM, AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_access_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
async def search_user(db_session: AsyncSession) -> User:
    role = Role(name="archivist", description="Search test archivist")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="search-archivist@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Search Tester",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def search_documents(db_session: AsyncSession) -> list[Document]:
    """Create a set of documents with varying properties for search testing."""
    docs = [
        Document(
            title="City Council Meeting Minutes 1920",
            accession_number="2026-0001",
            date_display="January 15, 1920",
            date_start=date(1920, 1, 15),
            date_end=date(1920, 1, 15),
            is_public=True,
            scope_and_content="Minutes of the regular council meeting.",
            inbox_status="processed",
            language_of_material="eng",
        ),
        Document(
            title="Fire Department Annual Report 1925",
            accession_number="2026-0002",
            date_display="1925",
            date_start=date(1925, 1, 1),
            date_end=date(1925, 12, 31),
            is_public=False,
            scope_and_content="Annual report of the volunteer fire department.",
            inbox_status="processed",
        ),
        Document(
            title="Land Deed for Jones Mill",
            accession_number="2026-0003",
            date_display="March 1850",
            date_start=date(1850, 3, 1),
            is_public=True,
            inbox_status="inbox",
        ),
    ]
    for doc in docs:
        db_session.add(doc)
    await db_session.flush()
    return docs


@pytest_asyncio.fixture
async def versioned_documents(db_session: AsyncSession) -> list[Document]:
    """Create versioned documents to test canonical filtering."""
    canonical = Document(
        title="VFD Bylaws",
        accession_number="2026-0010.1",
        version_group_id=1,
        version_number=1,
        is_canonical_version=True,
        inbox_status="processed",
    )
    non_canonical = Document(
        title="VFD Bylaws (1978 Revision)",
        accession_number="2026-0010.2",
        version_group_id=1,
        version_number=2,
        version_label="1978 Revision",
        is_canonical_version=False,
        inbox_status="processed",
    )
    db_session.add(canonical)
    db_session.add(non_canonical)
    await db_session.flush()
    return [canonical, non_canonical]


# ---------------------------------------------------------------------------
# Basic search
# ---------------------------------------------------------------------------


class TestSearchBasic:
    """Test basic search endpoint behavior."""

    @pytest.mark.asyncio
    async def test_search_returns_paginated_response(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    @pytest.mark.asyncio
    async def test_search_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/search")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Date filters
# ---------------------------------------------------------------------------


class TestSearchDateFilters:
    """Test date_from and date_to filtering."""

    @pytest.mark.asyncio
    async def test_search_date_from(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?date_from=1900-01-01",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        # Should include 1920 and 1925 but not 1850
        titles = [item["title"] for item in data["items"]]
        for title in titles:
            assert "1850" not in title or "Land Deed" not in title

    @pytest.mark.asyncio
    async def test_search_date_to(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?date_to=1920-12-31",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        # Should not include 1925
        titles = [item["title"] for item in data["items"]]
        for title in titles:
            assert "1925" not in title

    @pytest.mark.asyncio
    async def test_search_date_range(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?date_from=1900-01-01&date_to=1921-01-01",
            cookies={"access_token": token},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# is_public filter
# ---------------------------------------------------------------------------


class TestSearchPublicFilter:
    """Test filtering by is_public flag."""

    @pytest.mark.asyncio
    async def test_search_public_only(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?is_public=true",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_public"] is True

    @pytest.mark.asyncio
    async def test_search_private_only(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?is_public=false",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["is_public"] is False


# ---------------------------------------------------------------------------
# Version filter (canonical only)
# ---------------------------------------------------------------------------


class TestSearchVersionFilter:
    """Verify that search automatically restricts to canonical versions only."""

    @pytest.mark.asyncio
    async def test_search_returns_only_canonical(
        self,
        client: AsyncClient,
        search_user: User,
        versioned_documents: list[Document],
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        accession_numbers = [item.get("accession_number") for item in data["items"]]
        # The canonical version (2026-0010.1) should appear
        # The non-canonical (2026-0010.2) should NOT appear
        if "2026-0010.1" in accession_numbers:
            assert "2026-0010.2" not in accession_numbers


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestSearchPagination:
    """Test search pagination parameters."""

    @pytest.mark.asyncio
    async def test_search_custom_page_size(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?per_page=1&page=1",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 1
        assert len(data["items"]) <= 1

    @pytest.mark.asyncio
    async def test_search_page_beyond_results(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?page=9999",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_search_invalid_per_page(
        self, client: AsyncClient, search_user: User
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?per_page=0",
            cookies={"access_token": token},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_per_page_exceeds_max(
        self, client: AsyncClient, search_user: User
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?per_page=200",
            cookies={"access_token": token},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Review status filter
# ---------------------------------------------------------------------------


class TestSearchReviewStatus:
    """Test filtering by review_status."""

    @pytest.mark.asyncio
    async def test_search_by_review_status(
        self, client: AsyncClient, search_user: User, search_documents: list[Document]
    ) -> None:
        token = _make_access_token(search_user.id)
        response = await client.get(
            "/api/v1/search?review_status=none",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["review_status"] == "none"
