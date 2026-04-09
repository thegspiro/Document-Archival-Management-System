"""Event entity schemas — named historical occurrences."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    """Schema for POST /api/v1/events."""

    title: str = Field(min_length=1, max_length=500)
    event_type_id: int = Field(description="vocabulary_terms ID from 'event_type' domain")
    date_display: str | None = Field(default=None, max_length=200)
    date_start: date | None = None
    date_end: date | None = None
    primary_location_id: int | None = None
    description: str | None = None
    is_public: bool = False
    public_description: str | None = None


class EventUpdate(BaseModel):
    """Schema for PATCH /api/v1/events/{id}. All fields optional."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    event_type_id: int | None = None
    date_display: str | None = Field(default=None, max_length=200)
    date_start: date | None = None
    date_end: date | None = None
    primary_location_id: int | None = None
    description: str | None = None
    is_public: bool | None = None
    public_description: str | None = None


class EventResponse(BaseModel):
    """Full event response."""

    id: int
    title: str
    event_type_id: int
    date_display: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    primary_location_id: int | None = None
    description: str | None = None
    is_public: bool = False
    public_description: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventDocumentLinkCreate(BaseModel):
    """Schema for POST /api/v1/events/{id}/documents."""

    document_id: int
    link_type: str = Field(
        default="about",
        description="One of: produced_by, about, referenced_in, precedes, follows",
    )
    notes: str | None = None


class EventDocumentLinkResponse(BaseModel):
    """Response for an event-document link."""

    id: int
    event_id: int
    document_id: int
    link_type: str
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventAuthorityLinkCreate(BaseModel):
    """Schema for POST /api/v1/events/{id}/authorities."""

    authority_id: int
    role_id: int = Field(
        description="vocabulary_terms ID from 'event_authority_role' domain"
    )
    notes: str | None = None


class EventAuthorityLinkResponse(BaseModel):
    """Response for an event-authority link."""

    id: int
    event_id: int
    authority_id: int
    role_id: int
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventLocationLinkCreate(BaseModel):
    """Schema for POST /api/v1/events/{id}/locations."""

    location_id: int
    link_type: str = Field(
        default="primary",
        description="One of: primary, secondary, mentioned",
    )
    notes: str | None = None


class EventLocationLinkResponse(BaseModel):
    """Response for an event-location link."""

    id: int
    event_id: int
    location_id: int
    link_type: str
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
