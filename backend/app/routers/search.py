"""Search router — full-text and faceted search across documents.

Also hosts the bulk citation endpoint (POST /cite/bulk) which shares the
/api/v1 prefix with the search route.
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/search", response_model=PaginatedResponse[Any])
async def search_documents(
    q: str | None = Query(None, description="Full-text query"),
    creator_id: int | None = Query(None, description="Filter by authority record (creator)"),
    date_from: date | None = Query(None, description="Filter by date_start >="),
    date_to: date | None = Query(None, description="Filter by date_end <="),
    term_ids: list[int] | None = Query(None, description="Filter by vocabulary term IDs (AND)"),
    authority_ids: list[int] | None = Query(
        None, description="Filter by linked authority records (any role)"
    ),
    location_ids: list[int] | None = Query(None, description="Filter by linked locations"),
    event_ids: list[int] | None = Query(None, description="Filter by linked events"),
    node_id: int | None = Query(None, description="Filter to arrangement_node subtree"),
    document_type: str | None = Query(None, description="Vocabulary term in document_type domain"),
    language: str | None = Query(None, description="ISO 639 language code"),
    review_status: str | None = Query(None, description="Filter by review status"),
    is_public: bool | None = Query(None, description="Filter public/private"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Search documents with full-text query and faceted filters.

    Full-text search uses MySQL MATCH...AGAINST across title, scope_and_content,
    general_note, and OCR text. Results are ranked by relevance. Version filter
    automatically restricts to canonical versions only.
    """
    from app.services import search_service

    return await search_service.search(
        db,
        q=q,
        creator_id=creator_id,
        date_from=date_from,
        date_to=date_to,
        term_ids=term_ids,
        authority_ids=authority_ids,
        location_ids=location_ids,
        event_ids=event_ids,
        node_id=node_id,
        document_type=document_type,
        language=language,
        review_status=review_status,
        is_public=is_public,
        page=page,
        per_page=per_page,
        user=current_user,
    )


# ---------------------------------------------------------------------------
# Bulk citation export
# ---------------------------------------------------------------------------


class BulkCiteRequest(BaseModel):
    document_ids: list[int] = Field(min_length=1)
    format: str = Field(description="chicago_note|chicago_bib|turabian|bibtex|ris|zotero_rdf|csl_json")


@router.post("/cite/bulk")
async def bulk_cite(
    body: BulkCiteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Export citations for multiple documents as a single file (.bib, .ris, or JSON)."""
    from app.services import citation_service

    content, media_type, filename = await citation_service.bulk_cite(
        db, body.document_ids, body.format,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
