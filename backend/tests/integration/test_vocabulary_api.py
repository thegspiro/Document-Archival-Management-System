"""Integration tests for vocabulary CRUD and term merge endpoints.

Tests domain creation, term creation, term updates, term deletion,
and the term merge workflow.
"""

from datetime import datetime, timedelta, timezone

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
async def admin_user(db_session: AsyncSession) -> User:
    role = Role(name="admin", description="Admin role")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="vocab-admin@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Vocab Admin",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def archivist_user(db_session: AsyncSession) -> User:
    role = Role(name="archivist", description="Archivist role")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="vocab-archivist@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Vocab Archivist",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    role = Role(name="viewer", description="Viewer role")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="vocab-viewer@test.org",
        password_hash=AuthService.hash_password("password"),
        display_name="Vocab Viewer",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_domain(db_session: AsyncSession) -> VocabularyDomain:
    domain = VocabularyDomain(
        name="document_type",
        description="Types of documents",
        allows_user_addition=True,
    )
    db_session.add(domain)
    await db_session.flush()
    return domain


@pytest_asyncio.fixture
async def test_terms(
    db_session: AsyncSession, test_domain: VocabularyDomain
) -> list[VocabularyTerm]:
    terms = [
        VocabularyTerm(domain_id=test_domain.id, term="letter", sort_order=0),
        VocabularyTerm(domain_id=test_domain.id, term="photograph", sort_order=1),
        VocabularyTerm(domain_id=test_domain.id, term="leter", sort_order=2),  # typo for merge test
    ]
    for t in terms:
        db_session.add(t)
    await db_session.flush()
    return terms


# ---------------------------------------------------------------------------
# GET /api/v1/vocabulary/domains
# ---------------------------------------------------------------------------


class TestListDomains:
    """Test listing vocabulary domains."""

    @pytest.mark.asyncio
    async def test_list_domains(
        self, client: AsyncClient, archivist_user: User, test_domain: VocabularyDomain
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            "/api/v1/vocabulary/domains",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        domain_names = [d["name"] for d in data]
        assert "document_type" in domain_names

    @pytest.mark.asyncio
    async def test_list_domains_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/vocabulary/domains")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/vocabulary/domains
# ---------------------------------------------------------------------------


class TestCreateDomain:
    """Test domain creation (admin only)."""

    @pytest.mark.asyncio
    async def test_create_domain_as_admin(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.post(
            "/api/v1/vocabulary/domains",
            json={"name": "physical_format", "description": "Physical formats"},
            cookies={"access_token": token},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "physical_format"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_domain_duplicate_name(
        self, client: AsyncClient, admin_user: User, test_domain: VocabularyDomain
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.post(
            "/api/v1/vocabulary/domains",
            json={"name": "document_type"},
            cookies={"access_token": token},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_domain_as_archivist_forbidden(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            "/api/v1/vocabulary/domains",
            json={"name": "new_domain"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_domain_empty_name(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.post(
            "/api/v1/vocabulary/domains",
            json={"name": ""},
            cookies={"access_token": token},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/vocabulary/domains/{domain_id}/terms
# ---------------------------------------------------------------------------


class TestListTerms:
    """Test listing terms in a domain."""

    @pytest.mark.asyncio
    async def test_list_terms(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_domain: VocabularyDomain,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.get(
            f"/api/v1/vocabulary/domains/{test_domain.id}/terms",
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 3


# ---------------------------------------------------------------------------
# POST /api/v1/vocabulary/domains/{domain_id}/terms
# ---------------------------------------------------------------------------


class TestCreateTerm:
    """Test term creation."""

    @pytest.mark.asyncio
    async def test_create_term_as_archivist(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_domain: VocabularyDomain,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/domains/{test_domain.id}/terms",
            json={"term": "deed", "definition": "Legal property transfer document"},
            cookies={"access_token": token},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "deed"

    @pytest.mark.asyncio
    async def test_create_term_duplicate(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_domain: VocabularyDomain,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/domains/{test_domain.id}/terms",
            json={"term": "letter"},
            cookies={"access_token": token},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_create_term_as_viewer_forbidden(
        self,
        client: AsyncClient,
        viewer_user: User,
        test_domain: VocabularyDomain,
    ) -> None:
        token = _make_access_token(viewer_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/domains/{test_domain.id}/terms",
            json={"term": "map"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_term_empty_name(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_domain: VocabularyDomain,
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/domains/{test_domain.id}/terms",
            json={"term": ""},
            cookies={"access_token": token},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/v1/vocabulary/terms/{id}
# ---------------------------------------------------------------------------


class TestUpdateTerm:
    """Test term updates."""

    @pytest.mark.asyncio
    async def test_update_term_rename(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        typo_term = test_terms[2]  # "leter"
        token = _make_access_token(archivist_user.id)
        response = await client.patch(
            f"/api/v1/vocabulary/terms/{typo_term.id}",
            json={"term": "letter_corrected"},
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "letter_corrected"

    @pytest.mark.asyncio
    async def test_update_term_not_found(
        self, client: AsyncClient, archivist_user: User
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.patch(
            "/api/v1/vocabulary/terms/99999",
            json={"term": "nope"},
            cookies={"access_token": token},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_term_as_viewer_forbidden(
        self,
        client: AsyncClient,
        viewer_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(viewer_user.id)
        response = await client.patch(
            f"/api/v1/vocabulary/terms/{test_terms[0].id}",
            json={"term": "viewer attempt"},
            cookies={"access_token": token},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/vocabulary/terms/{id}
# ---------------------------------------------------------------------------


class TestDeleteTerm:
    """Test term deletion (admin only)."""

    @pytest.mark.asyncio
    async def test_delete_term_as_admin(
        self,
        client: AsyncClient,
        admin_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.delete(
            f"/api/v1/vocabulary/terms/{test_terms[1].id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_term_as_archivist_forbidden(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.delete(
            f"/api/v1/vocabulary/terms/{test_terms[0].id}",
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_term(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.delete(
            "/api/v1/vocabulary/terms/99999",
            cookies={"access_token": token},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/vocabulary/terms/{id}/merge
# ---------------------------------------------------------------------------


class TestMergeTerm:
    """Test the term merge endpoint."""

    @pytest.mark.asyncio
    async def test_merge_term_success(
        self,
        client: AsyncClient,
        admin_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        source = test_terms[2]  # "leter" (typo)
        target = test_terms[0]  # "letter" (correct)
        token = _make_access_token(admin_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/terms/{source.id}/merge",
            json={"into_term_id": target.id},
            cookies={"access_token": token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Merged" in data["detail"] or "merged" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_merge_term_into_itself(
        self,
        client: AsyncClient,
        admin_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        term = test_terms[0]
        token = _make_access_token(admin_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/terms/{term.id}/merge",
            json={"into_term_id": term.id},
            cookies={"access_token": token},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_merge_term_as_archivist_forbidden(
        self,
        client: AsyncClient,
        archivist_user: User,
        test_terms: list[VocabularyTerm],
    ) -> None:
        token = _make_access_token(archivist_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/terms/{test_terms[2].id}/merge",
            json={"into_term_id": test_terms[0].id},
            cookies={"access_token": token},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_merge_nonexistent_source(
        self, client: AsyncClient, admin_user: User, test_terms: list[VocabularyTerm]
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.post(
            "/api/v1/vocabulary/terms/99999/merge",
            json={"into_term_id": test_terms[0].id},
            cookies={"access_token": token},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_merge_nonexistent_target(
        self, client: AsyncClient, admin_user: User, test_terms: list[VocabularyTerm]
    ) -> None:
        token = _make_access_token(admin_user.id)
        response = await client.post(
            f"/api/v1/vocabulary/terms/{test_terms[0].id}/merge",
            json={"into_term_id": 99999},
            cookies={"access_token": token},
        )
        assert response.status_code == 404
