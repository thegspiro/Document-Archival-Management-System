"""Authentication service — login, JWT tokens, refresh, and revocation."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import jwt
from passlib.hash import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import RefreshToken, User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    """Handles credential verification, JWT issuance, refresh, and revocation.

    Access tokens expire in 15 minutes; refresh tokens in 30 days.  Both are
    delivered as httpOnly cookies — never in response bodies.
    """

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------

    @staticmethod
    def hash_password(password: str) -> str:
        """Return a bcrypt hash of *password*."""
        return bcrypt.hash(password)

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify *password* against a stored bcrypt hash."""
        return bcrypt.verify(password, password_hash)

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    @staticmethod
    def _create_access_token(user_id: int) -> tuple[str, datetime]:
        """Build a signed JWT access token and return (token, expiry)."""
        expires = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "exp": expires,
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        return token, expires

    @staticmethod
    def _create_refresh_token_value() -> str:
        """Generate a cryptographically random refresh token string."""
        return secrets.token_urlsafe(64)

    @staticmethod
    def _hash_token(token: str) -> str:
        """SHA-256 hash a refresh token for safe storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    async def authenticate(
        db: AsyncSession, *, email: str, password: str
    ) -> User:
        """Verify credentials and return the ``User`` or raise 401.

        Also updates ``last_login_at`` on success.
        """
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not AuthService.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
            )

        user.last_login_at = datetime.now(tz=timezone.utc)
        await db.flush()
        return user

    @staticmethod
    async def create_tokens(
        db: AsyncSession, user: User
    ) -> tuple[str, datetime, str]:
        """Issue a fresh access/refresh token pair.

        Returns ``(access_token, access_expires, refresh_token_raw)``.
        The caller is responsible for setting them as httpOnly cookies.
        """
        access_token, access_expires = AuthService._create_access_token(user.id)

        raw_refresh = AuthService._create_refresh_token_value()
        token_hash = AuthService._hash_token(raw_refresh)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_row = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(refresh_row)
        await db.flush()

        return access_token, access_expires, raw_refresh

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession, *, refresh_token_str: str
    ) -> tuple[str, datetime]:
        """Validate a refresh token and return a new access token.

        Returns ``(access_token, access_expires)``.
        Raises 401 if the refresh token is invalid, expired, or revoked.
        """
        token_hash = AuthService._hash_token(refresh_token_str)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        refresh_row = result.scalar_one_or_none()

        if refresh_row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
            )

        if refresh_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(tz=timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        access_token, access_expires = AuthService._create_access_token(refresh_row.user_id)
        return access_token, access_expires

    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, *, token_hash: str) -> None:
        """Mark a refresh token as revoked so it cannot be reused."""
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(tz=timezone.utc))
        )
        await db.flush()

    @staticmethod
    async def revoke_refresh_token_by_raw(db: AsyncSession, *, raw_token: str) -> None:
        """Revoke a refresh token given its raw (unhashed) value."""
        token_hash = AuthService._hash_token(raw_token)
        await AuthService.revoke_refresh_token(db, token_hash=token_hash)
