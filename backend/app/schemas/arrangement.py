"""Arrangement node schemas — hierarchical ISAD(G) levels."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LevelType = Literal["fonds", "subfonds", "series", "subseries", "file", "item"]


class ArrangementNodeCreate(BaseModel):
    """Schema for POST /api/v1/nodes."""

    parent_id: int | None = None
    level_type: LevelType
    title: str = Field(min_length=1, max_length=500)
    identifier: str | None = Field(default=None, max_length=200)
    description: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    is_public: bool = False
    sort_order: int = 0
    has_content_advisory: bool = False
    content_advisory_note: str | None = None


class ArrangementNodeUpdate(BaseModel):
    """Schema for PATCH /api/v1/nodes/{id}. All fields optional."""

    parent_id: int | None = None
    level_type: LevelType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    identifier: str | None = Field(default=None, max_length=200)
    description: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    is_public: bool | None = None
    sort_order: int | None = None
    has_content_advisory: bool | None = None
    content_advisory_note: str | None = None


class ArrangementNodeResponse(BaseModel):
    """Response schema for an arrangement node, including nested children."""

    id: int
    parent_id: int | None = None
    level_type: LevelType
    title: str
    identifier: str | None = None
    description: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    is_public: bool = False
    sort_order: int = 0
    has_content_advisory: bool = False
    content_advisory_note: str | None = None
    created_by: int | None = None
    children: list["ArrangementNodeResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Rebuild to resolve the self-referencing type
ArrangementNodeResponse.model_rebuild()
