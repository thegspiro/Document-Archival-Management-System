"""Authentication router — login, refresh, logout.

Tokens are delivered as httpOnly, SameSite=Strict cookies. No tokens appear
in response bodies or localStorage.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas local to auth
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """Email + password login credentials."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Returned on successful login (tokens are set as cookies, not in body)."""

    detail: str = "Login successful"
    user_id: int
    display_name: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Validate email/password, issue access + refresh tokens as httpOnly cookies."""
    from app.services import auth_service

    result = await auth_service.authenticate(db, body.email, body.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, refresh_token, user = result

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=15 * 60,  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=30 * 24 * 60 * 60,  # 30 days
    )

    return LoginResponse(user_id=user.id, display_name=user.display_name)


@router.post("/refresh", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> MessageResponse:
    """Issue a new access token from a valid refresh token cookie."""
    from app.services import auth_service

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )

    new_access_token = await auth_service.refresh_access_token(db, refresh_token)
    if new_access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=15 * 60,
    )

    return MessageResponse(detail="Token refreshed")


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Revoke the current refresh token and clear auth cookies."""
    from app.services import auth_service

    await auth_service.revoke_refresh_tokens(db, current_user.id)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return MessageResponse(detail="Logged out")
