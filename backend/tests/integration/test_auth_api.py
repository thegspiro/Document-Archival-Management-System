"""Integration tests for auth endpoints — login, refresh, logout.

These tests use the real FastAPI test client with the database session
overridden by the test fixture in conftest.py.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User, UserRole
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create an active test user with the 'archivist' role."""
    role = Role(name="archivist", description="Test archivist")
    db_session.add(role)
    await db_session.flush()

    user = User(
        email="archivist@example.org",
        password_hash=AuthService.hash_password("secure-password-123"),
        display_name="Test Archivist",
        is_active=True,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.flush()

    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create a deactivated test user."""
    user = User(
        email="inactive@example.org",
        password_hash=AuthService.hash_password("password-456"),
        display_name="Inactive User",
        is_active=False,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    """Test the login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "archivist@example.org", "password": "secure-password-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detail"] == "Login successful"
        assert data["user_id"] == test_user.id
        assert data["display_name"] == "Test Archivist"

        # Verify cookies are set
        cookies = response.cookies
        assert "access_token" in cookies or response.headers.get("set-cookie") is not None

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "archivist@example.org", "password": "wrong-password"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.org", "password": "any"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self, client: AsyncClient, inactive_user: User
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.org", "password": "password-456"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.org"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_empty_body(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------


class TestRefresh:
    """Test the token refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_without_cookie(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_cookie(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": "invalid-token-value"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout
# ---------------------------------------------------------------------------


class TestLogout:
    """Test the logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_without_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")
        # Should fail because the user is not authenticated
        assert response.status_code == 401
