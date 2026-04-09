"""Integration tests for document CRUD endpoints.

Tests POST /documents, GET /documents, GET /documents/{id},
PATCH /documents/{id}, DELETE /documents/{id}, and permission enforcement.
"""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.arrangement import ArrangementNode
from app.models.document import Document
from app.models.user import Role, User, UserRole
from app.services.auth_service import ALGORITHM, AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_access_token(user_id: int) -> str:
    """Create a valid JWT access token for testing."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=15),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
async def archivist_role(db_session: AsyncSession) -> Role:
    role = Role(name="archivist", description="Archivist role")
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def viewer_role(db_session: AsyncSession) -> Role:
    role = Role(name="viewer", description="Viewer role")
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Role:
    role = Role(name="admin", description="Admin role")
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def archivist_user(db_session: AsyncSession, archivist_role: Role) -> User:
    user = User(
        email="archivist@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Archivist",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=archivist_role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession, viewer_role: Role) -> User:
    user = User(
        email="viewer@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Viewer",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=viewer_role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_role: Role) -> User:
    user = User(
        email="admin@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Admin",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def superadmin_user(db_session: AsyncSession) -> User:
    user = User(
        email="superadmin@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Superadmin",
        is_active=True,
        is_superadmin=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def sample_document(db_session: AsyncSession) -> Document:
    doc = Document(
        title="Test Letter",
        accession_number="2026-0001",
        inbox_status="inbox",
        description_status="draft",
    )
    db_session.add(doc)
    await db_session.flush()
    return doc


# ---------------------------------------------------------------------------
# POST /api/v1/documents
# ---------------------------------------------------------------------------


class TestCreateDocument:
    """Test document creation."""

    @pytest.mark.asyncio
    async def test_create_document_as_archivist(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            "/api/v1/documents",
            json={"title": "New Council Minutes"},
            cookies={"access_token": token},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Council Minutes"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_document_viewer_forbidden(
        self, client: AsyncClient, viewer_user: User
    ) -> None:
        token = _make_access_token(viewer_user.id)
        response = await client.post(
            "/api/v1/documents",
            json={"title": "Should Not Be Created"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_document_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/documents",
            json={"title": "No Auth"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_document_empty_title(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            "/api/v1/documents",
            json={"title": ""},
            cookies={"access_token": token},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_document_with_optional_fields(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            "/api/v1/documents",
            json={
                "title": "Historical Map",
                "date_display": "1885",
                "extent": "1 sheet",
                "language_of_material": "eng",
            },
            cookies={"access_token": token},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Historical Map"

    @pytest.mark.asyncio
    async def test_create_as_superadmin(
        self, client: AsyncClient, superadmin_user: User
    ) -> None:
        token = _make_access_token(superadmin_user.id)
        response = await client.post(
            "/api/v1/documents",
            json={"title": "Superadmin Document"},
            cookies={"access_token": token},
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/v1/documents
# ---------------------------------------------------------------------------


class TestListDocuments:
    """Test document listing."""

    @pytest.mark.asyncio
    async def test_list_documents(
        self,
        client: AsyncClient,
        archivist_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            "/api/v1/documents",
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
    async def test_list_documents_pagination(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            "/api/v1/documents?page=1&per_page=5",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 5

    @pytest.mark.asyncio
    async def test_list_documents_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/documents")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{id}
# ---------------------------------------------------------------------------


class TestGetDocument:
    """Test single document retrieval."""

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        client: AsyncClient,
        archivist_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            f"/api/v1/documents/{sample_document.id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["title"] == "Test Letter"

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            "/api/v1/documents/99999",
            cookies={"access_token": token},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/documents/{id}
# ---------------------------------------------------------------------------


class TestUpdateDocument:
    """Test document updates."""

    @pytest.mark.asyncio
    async def test_update_document_title(
        self,
        client: AsyncClient,
        archivist_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.patch(
            f"/api/v1/documents/{sample_document.id}",
            json={"title": "Updated Title"},
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_document_viewer_forbidden(
        self,
        client: AsyncClient,
        viewer_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(viewer_user.id)
        response = await client.patch(
            f"/api/v1/documents/{sample_document.id}",
            json={"title": "Viewer Attempt"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.patch(
            "/api/v1/documents/99999",
            json={"title": "No Such Doc"},
            cookies={"access_token": token},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/documents/{id}
# ---------------------------------------------------------------------------


class TestDeleteDocument:
    """Test document deletion (admin only)."""

    @pytest.mark.asyncio
    async def test_delete_as_admin(
        self,
        client: AsyncClient,
        admin_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.delete(
            f"/api/v1/documents/{sample_document.id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_as_archivist_forbidden(
        self,
        client: AsyncClient,
        archivist_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.delete(
            f"/api/v1/documents/{sample_document.id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_as_viewer_forbidden(
        self,
        client: AsyncClient,
        viewer_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(viewer_user.id)
        response = await client.delete(
            f"/api/v1/documents/{sample_document.id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.delete(
            "/api/v1/documents/99999",
            cookies={"access_token": token},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_as_superadmin(
        self,
        client: AsyncClient,
        superadmin_user: User,
        sample_document: Document,
    ) -> None:
        token = _make_access_token(superadmin_user.id)
        response = await client.delete(
            f"/api/v1/documents/{sample_document.id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 204
