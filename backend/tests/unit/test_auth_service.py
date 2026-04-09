"""Unit tests for AuthService — password hashing, JWT tokens, refresh, revocation."""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt

from app.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    AuthService,
)


# ---------------------------------------------------------------------------
# Password hashing and verification
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    """Verify bcrypt password hashing and verification."""

    def test_hash_password_returns_bcrypt_hash(self) -> None:
        hashed = AuthService.hash_password("correct-horse-battery-staple")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert hashed != "correct-horse-battery-staple"

    def test_verify_password_correct(self) -> None:
        password = "archival-metadata-2025"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        hashed = AuthService.hash_password("real-password")
        assert AuthService.verify_password("wrong-password", hashed) is False

    def test_hash_password_unique_salts(self) -> None:
        """Two calls with the same password produce different hashes (unique salts)."""
        h1 = AuthService.hash_password("same-password")
        h2 = AuthService.hash_password("same-password")
        assert h1 != h2

    def test_verify_password_empty_string(self) -> None:
        hashed = AuthService.hash_password("")
        assert AuthService.verify_password("", hashed) is True
        assert AuthService.verify_password("non-empty", hashed) is False


# ---------------------------------------------------------------------------
# Token creation helpers
# ---------------------------------------------------------------------------


class TestTokenCreation:
    """Verify JWT access token creation and refresh token generation."""

    @patch("app.services.auth_service.settings")
    def test_create_access_token_structure(self, mock_settings: MagicMock) -> None:
        mock_settings.SECRET_KEY = "test-secret-key-64-chars-long-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        token, expires = AuthService._create_access_token(user_id=42)
        payload = jwt.decode(token, mock_settings.SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == 42
        assert payload["type"] == "access"
        assert "exp" in payload

    @patch("app.services.auth_service.settings")
    def test_create_access_token_expiry(self, mock_settings: MagicMock) -> None:
        mock_settings.SECRET_KEY = "test-secret-key-64-chars-long-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        before = datetime.now(tz=timezone.utc)
        _, expires = AuthService._create_access_token(user_id=1)
        after = datetime.now(tz=timezone.utc)

        expected_min = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expected_max = after + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        assert expected_min <= expires <= expected_max

    def test_create_refresh_token_value_uniqueness(self) -> None:
        t1 = AuthService._create_refresh_token_value()
        t2 = AuthService._create_refresh_token_value()
        assert t1 != t2

    def test_create_refresh_token_value_length(self) -> None:
        token = AuthService._create_refresh_token_value()
        assert len(token) > 40  # url-safe base64 of 64 bytes

    def test_hash_token_sha256(self) -> None:
        raw = "test-token-value"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert AuthService._hash_token(raw) == expected

    def test_hash_token_deterministic(self) -> None:
        raw = "deterministic-test"
        assert AuthService._hash_token(raw) == AuthService._hash_token(raw)


# ---------------------------------------------------------------------------
# Authenticate
# ---------------------------------------------------------------------------


class TestAuthenticate:
    """Test the authenticate method with mocked DB session."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        password = "secure-password-123"
        hashed = AuthService.hash_password(password)

        mock_user = MagicMock()
        mock_user.email = "archivist@example.org"
        mock_user.password_hash = hashed
        mock_user.is_active = True
        mock_user.last_login_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user

        db = AsyncMock()
        db.execute.return_value = mock_result

        user = await AuthService.authenticate(db, email="archivist@example.org", password=password)
        assert user is mock_user
        assert mock_user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self) -> None:
        hashed = AuthService.hash_password("correct-password")

        mock_user = MagicMock()
        mock_user.password_hash = hashed
        mock_user.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.authenticate(db, email="user@example.org", password="wrong")
        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.authenticate(db, email="nonexistent@example.org", password="any")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self) -> None:
        password = "correct-password"
        hashed = AuthService.hash_password(password)

        mock_user = MagicMock()
        mock_user.password_hash = hashed
        mock_user.is_active = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.authenticate(db, email="inactive@example.org", password=password)
        assert exc_info.value.status_code == 401
        assert "deactivated" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Create tokens
# ---------------------------------------------------------------------------


class TestCreateTokens:
    """Test the create_tokens method (issues both access and refresh tokens)."""

    @pytest.mark.asyncio
    @patch("app.services.auth_service.settings")
    async def test_create_tokens_returns_three_values(self, mock_settings: MagicMock) -> None:
        mock_settings.SECRET_KEY = "test-secret-key-64-chars-long-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        mock_user = MagicMock()
        mock_user.id = 7

        db = AsyncMock()

        access_token, access_expires, refresh_raw = await AuthService.create_tokens(db, mock_user)

        assert isinstance(access_token, str)
        assert isinstance(access_expires, datetime)
        assert isinstance(refresh_raw, str)
        assert len(refresh_raw) > 40

    @pytest.mark.asyncio
    @patch("app.services.auth_service.settings")
    async def test_create_tokens_saves_refresh_hash_to_db(self, mock_settings: MagicMock) -> None:
        mock_settings.SECRET_KEY = "test-secret-key-64-chars-long-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        mock_user = MagicMock()
        mock_user.id = 5

        db = AsyncMock()

        _, _, refresh_raw = await AuthService.create_tokens(db, mock_user)

        # A RefreshToken was added to the session
        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert added_obj.user_id == 5
        assert added_obj.token_hash == AuthService._hash_token(refresh_raw)


# ---------------------------------------------------------------------------
# Refresh access token
# ---------------------------------------------------------------------------


class TestRefreshAccessToken:
    """Test refresh token validation and new access token issuance."""

    @pytest.mark.asyncio
    @patch("app.services.auth_service.settings")
    async def test_refresh_success(self, mock_settings: MagicMock) -> None:
        mock_settings.SECRET_KEY = "test-secret-key-64-chars-long-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        raw_token = "valid-refresh-token"

        mock_refresh_row = MagicMock()
        mock_refresh_row.user_id = 10
        mock_refresh_row.expires_at = datetime.now(tz=timezone.utc) + timedelta(days=15)
        mock_refresh_row.revoked_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_refresh_row

        db = AsyncMock()
        db.execute.return_value = mock_result

        access_token, access_expires = await AuthService.refresh_access_token(
            db, refresh_token_str=raw_token
        )
        assert isinstance(access_token, str)
        assert isinstance(access_expires, datetime)

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.refresh_access_token(db, refresh_token_str="bad-token")
        assert exc_info.value.status_code == 401
        assert "Invalid or revoked" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self) -> None:
        mock_refresh_row = MagicMock()
        mock_refresh_row.user_id = 10
        mock_refresh_row.expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_refresh_row

        db = AsyncMock()
        db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await AuthService.refresh_access_token(db, refresh_token_str="expired-token")
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# Revoke refresh token
# ---------------------------------------------------------------------------


class TestRevokeRefreshToken:
    """Test refresh token revocation."""

    @pytest.mark.asyncio
    async def test_revoke_by_hash(self) -> None:
        db = AsyncMock()
        await AuthService.revoke_refresh_token(db, token_hash="abc123hash")
        db.execute.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_by_raw(self) -> None:
        db = AsyncMock()
        raw = "raw-token-string"
        await AuthService.revoke_refresh_token_by_raw(db, raw_token=raw)
        db.execute.assert_called_once()
        db.flush.assert_called_once()
