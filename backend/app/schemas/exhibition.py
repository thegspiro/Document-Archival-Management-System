"""Exhibition schemas — exhibitions, pages, and content blocks."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

import re


BlockType = Literal[
    "html", "file_with_text", "gallery", "document_metadata",
    "map", "timeline", "table_of_contents", "collection_browse", "separator",
]
BlockLayout = Literal["full", "left", "right", "center"]


# ---------------------------------------------------------------------------
# Exhibition
# ---------------------------------------------------------------------------

class ExhibitionCreate(BaseModel):
    """Schema for POST /api/v1/exhibitions."""

    title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = None
    credits: str | None = None
    cover_image_path: str | None = Field(default=None, max_length=2000)
    header_image_path: str | None = Field(default=None, max_length=2000)
    accent_color: str | None = Field(
        default=None,
        max_length=7,
        description="Hex color for per-exhibit theming, e.g. '#8B1A1A'",
    )
    show_summary_page: bool = True
    is_published: bool = False
    sort_order: int = 0
    tag_ids: list[int] = Field(
        default_factory=list,
        description="vocabulary_terms IDs from 'tag' domain to attach as exhibition tags",
    )

    @field_validator("accent_color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("accent_color must be a valid 7-character hex color (e.g. '#8B1A1A')")
        return v


class ExhibitionUpdate(BaseModel):
    """Schema for PATCH /api/v1/exhibitions/{id}. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    subtitle: str | None = Field(default=None, max_length=500)
    description: str | None = None
    credits: str | None = None
    cover_image_path: str | None = Field(default=None, max_length=2000)
    header_image_path: str | None = Field(default=None, max_length=2000)
    accent_color: str | None = Field(default=None, max_length=7)
    show_summary_page: bool | None = None
    is_published: bool | None = None
    sort_order: int | None = None
    tag_ids: list[int] | None = None

    @field_validator("accent_color")
    @classmethod
    def validate_hex_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("accent_color must be a valid 7-character hex color (e.g. '#8B1A1A')")
        return v


class ExhibitionResponse(BaseModel):
    """Full exhibition response including pages and tags."""

    id: int
    title: str
    slug: str
    subtitle: str | None = None
    description: str | None = None
    credits: str | None = None
    cover_image_path: str | None = None
    header_image_path: str | None = None
    accent_color: str | None = None
    show_summary_page: bool = True
    is_published: bool = False
    published_at: datetime | None = None
    sort_order: int = 0
    created_by: int | None = None
    tag_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Exhibition Page
# ---------------------------------------------------------------------------

class ExhibitionPageCreate(BaseModel):
    """Schema for POST /api/v1/exhibitions/{id}/pages."""

    parent_page_id: int | None = None
    title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    menu_title: str | None = Field(default=None, max_length=200)
    is_public: bool = True
    sort_order: int = 0


class ExhibitionPageUpdate(BaseModel):
    """Schema for PATCH /api/v1/exhibitions/{id}/pages/{page_id}. All fields optional."""

    parent_page_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    menu_title: str | None = Field(default=None, max_length=200)
    is_public: bool | None = None
    sort_order: int | None = None


class ExhibitionPageResponse(BaseModel):
    """Response for an exhibition page including its content blocks."""

    id: int
    exhibition_id: int
    parent_page_id: int | None = None
    title: str
    slug: str
    menu_title: str | None = None
    is_public: bool = True
    sort_order: int = 0
    blocks: list["ExhibitionPageBlockResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Exhibition Page Block
# ---------------------------------------------------------------------------

class ExhibitionPageBlockCreate(BaseModel):
    """Schema for POST /api/v1/exhibitions/{id}/pages/{page_id}/blocks.

    The ``content`` JSON structure varies by ``block_type`` and is validated
    at the service layer per the block content specification in CLAUDE.md §12.5.
    """

    block_type: BlockType
    content: dict[str, Any] = Field(description="Block-type-specific configuration JSON")
    layout: BlockLayout = "full"
    sort_order: int = 0


class ExhibitionPageBlockUpdate(BaseModel):
    """Schema for PATCH /api/v1/exhibitions/{id}/pages/{page_id}/blocks/{block_id}."""

    block_type: BlockType | None = None
    content: dict[str, Any] | None = None
    layout: BlockLayout | None = None
    sort_order: int | None = None


class ExhibitionPageBlockResponse(BaseModel):
    """Response for a single content block within an exhibition page."""

    id: int
    page_id: int
    block_type: BlockType
    content: dict[str, Any]
    layout: BlockLayout = "full"
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockReorderRequest(BaseModel):
    """Schema for POST /api/v1/exhibitions/{id}/pages/{page_id}/blocks/reorder."""

    block_ids: list[int] = Field(
        min_length=1,
        description="Ordered list of block IDs representing the desired sort order",
    )


# Rebuild to resolve forward reference
ExhibitionPageResponse.model_rebuild()
