"""Search request and response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


class SearchRequest(BaseModel):
    """Query parameters for GET /api/v1/search.

    All parameters are optional. When multiple filters are supplied they are
    combined with AND logic.
    """

    q: str | None = Field(
        default=None,
        description="Full-text query across title, OCR text, scope_and_content, and notes",
    )
    creator_id: int | None = Field(default=None, description="Filter by authority record ID")
    date_from: date | None = None
    date_to: date | None = None
    term_ids: list[int] | None = Field(
        default=None, description="Filter by vocabulary term IDs (AND logic)"
    )
    authority_ids: list[int] | None = Field(
        default=None,
        description="Filter by linked authority records (any role, including creator)",
    )
    location_ids: list[int] | None = Field(
        default=None, description="Filter by linked location records"
    )
    event_ids: list[int] | None = Field(
        default=None, description="Filter by linked events"
    )
    node_id: int | None = Field(
        default=None, description="Filter to a subtree of arrangement_nodes"
    )
    document_type: str | None = Field(
        default=None, description="Vocabulary term in the document_type domain"
    )
    language: str | None = Field(default=None, description="ISO 639 language code")
    review_status: Literal["none", "pending", "approved", "rejected"] | None = None
    is_public: bool | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)


class SearchHit(BaseModel):
    """A single search result with relevance score and minimal metadata."""

    id: int
    accession_number: str | None = None
    title: str
    date_display: str | None = None
    date_start: date | None = None
    creator_id: int | None = None
    creator_name: str | None = Field(
        default=None, description="Denormalized creator name for display"
    )
    description_completeness: str | None = None
    is_public: bool = False
    thumbnail_url: str | None = None
    relevance_score: float | None = Field(
        default=None,
        description="MySQL MATCH ... AGAINST relevance score, if full-text search was used",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(PaginatedResponse[SearchHit]):
    """Paginated search results."""

    pass
