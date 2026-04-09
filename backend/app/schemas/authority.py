"""Authority record schemas — persons, organizations, families."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


EntityType = Literal["person", "organization", "family"]


class AuthorityRecordCreate(BaseModel):
    """Schema for POST /api/v1/authority."""

    entity_type: EntityType
    authorized_name: str = Field(min_length=1, max_length=500)
    variant_names: str | None = Field(
        default=None,
        description="Pipe-delimited alternate names, e.g. 'J. Smith|John W. Smith'",
    )
    dates: str | None = Field(default=None, max_length=200)
    biographical_history: str | None = None
    administrative_history: str | None = None
    identifier: str | None = Field(default=None, max_length=200)
    sources: str | None = None
    notes: str | None = None
    is_public: bool = False


class AuthorityRecordUpdate(BaseModel):
    """Schema for PATCH /api/v1/authority/{id}. All fields optional."""

    entity_type: EntityType | None = None
    authorized_name: str | None = Field(default=None, min_length=1, max_length=500)
    variant_names: str | None = None
    dates: str | None = Field(default=None, max_length=200)
    biographical_history: str | None = None
    administrative_history: str | None = None
    identifier: str | None = Field(default=None, max_length=200)
    sources: str | None = None
    notes: str | None = None
    is_public: bool | None = None
    wikidata_qid: str | None = Field(default=None, max_length=20)


class AuthorityRecordResponse(BaseModel):
    """Full authority record response with Wikidata and NER provenance."""

    id: int
    entity_type: EntityType
    authorized_name: str
    variant_names: str | None = None
    dates: str | None = None
    biographical_history: str | None = None
    administrative_history: str | None = None
    identifier: str | None = None
    sources: str | None = None
    notes: str | None = None
    is_public: bool = False

    # Wikidata
    wikidata_qid: str | None = None
    wikidata_last_synced_at: datetime | None = None
    wikidata_enrichment: dict[str, Any] | None = None

    # NER provenance
    created_by_ner: bool = False
    created_by: int | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthorityRelationshipCreate(BaseModel):
    """Schema for POST /api/v1/authority/{id}/relationships."""

    target_authority_id: int
    relationship_type_id: int = Field(
        description="vocabulary_terms ID from 'authority_relationship_type' domain"
    )
    date_start: str | None = Field(default=None, max_length=200)
    date_end: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class AuthorityRelationshipResponse(BaseModel):
    """Response for a relationship between two authority records."""

    id: int
    source_authority_id: int
    target_authority_id: int
    relationship_type_id: int
    date_start: str | None = None
    date_end: str | None = None
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WikidataLinkRequest(BaseModel):
    """Schema for POST /api/v1/authority/{id}/wikidata/link."""

    qid: str = Field(
        min_length=2,
        max_length=20,
        pattern=r"^Q\d+$",
        description="Wikidata Q identifier, e.g. 'Q42'",
    )
