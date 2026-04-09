"""Authority records router — CRUD for persons, organizations, and families.

Also handles document links, authority-to-authority relationships, events,
Wikidata integration, and NER suggestions.
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


class AuthorityCreate(BaseModel):
    entity_type: str = Field(description="person | organization | family")
    authorized_name: str = Field(min_length=1, max_length=500)
    variant_names: str | None = None
    dates: str | None = None
    biographical_history: str | None = None
    administrative_history: str | None = None
    identifier: str | None = None
    sources: str | None = None
    notes: str | None = None
    is_public: bool = False


class AuthorityUpdate(BaseModel):
    entity_type: str | None = None
    authorized_name: str | None = None
    variant_names: str | None = None
    dates: str | None = None
    biographical_history: str | None = None
    administrative_history: str | None = None
    identifier: str | None = None
    sources: str | None = None
    notes: str | None = None
    is_public: bool | None = None


class AuthorityOut(BaseModel):
    id: int
    entity_type: str
    authorized_name: str
    variant_names: str | None = None
    dates: str | None = None
    is_public: bool = False
    wikidata_qid: str | None = None
    created_by_ner: bool = False

    class Config:
        from_attributes = True


class AuthorityRelationshipCreate(BaseModel):
    target_authority_id: int
    relationship_type_id: int
    date_start: str | None = None
    date_end: str | None = None
    notes: str | None = None


class AuthorityRelationshipOut(BaseModel):
    id: int
    source_authority_id: int
    target_authority_id: int
    relationship_type_id: int
    date_start: str | None = None
    date_end: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True


class WikidataLinkRequest(BaseModel):
    qid: str = Field(description="Wikidata Q identifier, e.g. Q42")


class NerSuggestionOut(BaseModel):
    id: int
    entity_type: str
    authorized_name: str
    created_by_ner: bool = True

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[AuthorityOut])
async def list_authority_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    entity_type: str | None = Query(None, description="person|organization|family"),
    q: str | None = Query(None, description="Name search"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List authority records with pagination and optional filters."""
    from app.services import authority_service

    return await authority_service.list_records(
        db, page=page, per_page=per_page, entity_type=entity_type, q=q,
    )


@router.post("", response_model=AuthorityOut, status_code=status.HTTP_201_CREATED)
async def create_authority_record(
    body: AuthorityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a new authority record."""
    from app.services import authority_service

    return await authority_service.create_record(db, body, current_user)


@router.get("/{authority_id}", response_model=AuthorityOut)
async def get_authority_record(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single authority record by ID."""
    from app.services import authority_service

    record = await authority_service.get_record(db, authority_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority record not found"
        )
    return record


@router.patch("/{authority_id}", response_model=AuthorityOut)
async def update_authority_record(
    authority_id: int,
    body: AuthorityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update an authority record."""
    from app.services import authority_service

    record = await authority_service.update_record(db, authority_id, body, current_user)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority record not found"
        )
    return record


@router.delete("/{authority_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_authority_record(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete an authority record."""
    from app.services import authority_service

    success = await authority_service.delete_record(db, authority_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority record not found"
        )


# ---------------------------------------------------------------------------
# Documents linked to authority
# ---------------------------------------------------------------------------


@router.get("/{authority_id}/documents", response_model=PaginatedResponse[Any])
async def list_authority_documents(
    authority_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List documents where this authority record is the ISAD(G) creator."""
    from app.services import authority_service

    return await authority_service.list_documents(
        db, authority_id, page=page, per_page=per_page,
    )


@router.get("/{authority_id}/document-links", response_model=list[Any])
async def list_authority_document_links(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all document links for this authority (any role)."""
    from app.services import authority_service

    return await authority_service.list_document_links(db, authority_id)


# ---------------------------------------------------------------------------
# Authority-to-authority relationships
# ---------------------------------------------------------------------------


@router.get(
    "/{authority_id}/relationships",
    response_model=list[AuthorityRelationshipOut],
)
async def list_authority_relationships(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List relationships to/from this authority record."""
    from app.services import authority_service

    return await authority_service.list_relationships(db, authority_id)


@router.post(
    "/{authority_id}/relationships",
    response_model=AuthorityRelationshipOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_authority_relationship(
    authority_id: int,
    body: AuthorityRelationshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a relationship between two authority records."""
    from app.services import authority_service

    return await authority_service.create_relationship(
        db, authority_id, body, current_user
    )


@router.delete(
    "/{authority_id}/relationships/{rel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_authority_relationship(
    authority_id: int,
    rel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove an authority-to-authority relationship."""
    from app.services import authority_service

    success = await authority_service.delete_relationship(
        db, authority_id, rel_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found"
        )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.get("/{authority_id}/events", response_model=list[Any])
async def list_authority_events(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List events linked to this authority record."""
    from app.services import authority_service

    return await authority_service.list_events(db, authority_id)


# ---------------------------------------------------------------------------
# Wikidata
# ---------------------------------------------------------------------------


@router.get("/{authority_id}/wikidata")
async def get_wikidata_enrichment(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Fetch live Wikidata enrichment data for an authority record."""
    from app.services import wikidata_service

    result = await wikidata_service.fetch_enrichment(db, authority_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authority record not found or not linked to Wikidata",
        )
    return result


@router.post(
    "/{authority_id}/wikidata/link",
    response_model=MessageResponse,
)
async def link_wikidata(
    authority_id: int,
    body: WikidataLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Link an authority record to a Wikidata entity and cache enrichment."""
    from app.services import wikidata_service

    await wikidata_service.link(db, authority_id, body.qid, current_user)
    return MessageResponse(detail="Wikidata link created")


@router.delete(
    "/{authority_id}/wikidata/link",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_wikidata(
    authority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> None:
    """Remove the Wikidata link from an authority record."""
    from app.services import wikidata_service

    success = await wikidata_service.unlink(db, authority_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority record not found"
        )


# ---------------------------------------------------------------------------
# NER suggestions
# ---------------------------------------------------------------------------


@router.get("/ner-suggestions", response_model=PaginatedResponse[NerSuggestionOut])
async def list_ner_suggestions(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """List authority records created by NER that are pending review."""
    from app.services import ner_service

    return await ner_service.list_suggestions(db, page=page, per_page=per_page)


@router.post(
    "/ner-suggestions/{suggestion_id}/accept",
    response_model=MessageResponse,
)
async def accept_ner_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Accept a NER-suggested authority record, marking it as reviewed."""
    from app.services import ner_service

    await ner_service.accept_suggestion(db, suggestion_id, current_user)
    return MessageResponse(detail="NER suggestion accepted")


@router.post(
    "/ner-suggestions/{suggestion_id}/reject",
    response_model=MessageResponse,
)
async def reject_ner_suggestion(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Reject and remove a NER-suggested authority record."""
    from app.services import ner_service

    await ner_service.reject_suggestion(db, suggestion_id, current_user)
    return MessageResponse(detail="NER suggestion rejected")
