"""Controlled vocabulary domain and term schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VocabularyDomainCreate(BaseModel):
    """Schema for POST /api/v1/vocabulary/domains."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    allows_user_addition: bool = True


class VocabularyDomainResponse(BaseModel):
    """Response schema for a vocabulary domain with its terms."""

    id: int
    name: str
    description: str | None = None
    allows_user_addition: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VocabularyTermCreate(BaseModel):
    """Schema for POST /api/v1/vocabulary/domains/{domain_id}/terms."""

    term: str = Field(min_length=1, max_length=500)
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool = True
    sort_order: int = 0


class VocabularyTermUpdate(BaseModel):
    """Schema for PATCH /api/v1/vocabulary/terms/{id}. All fields optional."""

    term: str | None = Field(default=None, min_length=1, max_length=500)
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class VocabularyTermResponse(BaseModel):
    """Full vocabulary term response."""

    id: int
    domain_id: int
    term: str
    definition: str | None = None
    broader_term_id: int | None = None
    is_active: bool = True
    sort_order: int = 0
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TermMergeRequest(BaseModel):
    """Schema for POST /api/v1/vocabulary/terms/{id}/merge."""

    into_term_id: int = Field(description="Target term ID to merge this term into")
