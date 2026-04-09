"""Controlled vocabulary router — domains and terms management.

Covers domain CRUD, term CRUD, and the term merge workflow for bulk corrections.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class DomainCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    allows_user_addition: bool = True


class DomainOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    allows_user_addition: bool = True

    class Config:
        from_attributes = True


class TermCreate(BaseModel):
    term: str = Field(min_length=1, max_length=500)
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool = True
    sort_order: int = 0


class TermUpdate(BaseModel):
    term: str | None = None
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class TermOut(BaseModel):
    id: int
    domain_id: int
    term: str
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool = True
    sort_order: int = 0

    class Config:
        from_attributes = True


class TermMergeRequest(BaseModel):
    into_term_id: int = Field(description="ID of the term to merge INTO")


# ---------------------------------------------------------------------------
# Domains
# ---------------------------------------------------------------------------


@router.get("/domains", response_model=list[DomainOut])
async def list_domains(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all vocabulary domains."""
    from app.services import vocabulary_service

    return await vocabulary_service.list_domains(db)


@router.post(
    "/domains",
    response_model=DomainOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_domain(
    body: DomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Create a new vocabulary domain. Admin only."""
    from app.services import vocabulary_service

    return await vocabulary_service.create_domain(db, body, current_user)


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------


@router.get("/domains/{domain_id}/terms", response_model=PaginatedResponse[TermOut])
async def list_terms(
    domain_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    q: str | None = Query(None, description="Search within terms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List terms in a vocabulary domain with optional search."""
    from app.services import vocabulary_service

    return await vocabulary_service.list_terms(
        db, domain_id, page=page, per_page=per_page, q=q,
    )


@router.post(
    "/domains/{domain_id}/terms",
    response_model=TermOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_term(
    domain_id: int,
    body: TermCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Create a new vocabulary term in a domain."""
    from app.services import vocabulary_service

    return await vocabulary_service.create_term(db, domain_id, body, current_user)


@router.patch("/terms/{term_id}", response_model=TermOut)
async def update_term(
    term_id: int,
    body: TermUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Update a vocabulary term (rename, deactivate, reclassify)."""
    from app.services import vocabulary_service

    term = await vocabulary_service.update_term(db, term_id, body, current_user)
    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Term not found"
        )
    return term


@router.delete("/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(
    term_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete a vocabulary term. Fails if the term is in use on documents."""
    from app.services import vocabulary_service

    success = await vocabulary_service.delete_term(db, term_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Term not found"
        )


@router.post(
    "/terms/{term_id}/merge",
    response_model=MessageResponse,
)
async def merge_term(
    term_id: int,
    body: TermMergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> MessageResponse:
    """Merge term_id into into_term_id, reassigning all document associations."""
    from app.services import vocabulary_service

    result = await vocabulary_service.merge_term(
        db, term_id, body.into_term_id, current_user
    )
    return MessageResponse(
        detail=f"Merged term into target; {result} documents updated"
    )
