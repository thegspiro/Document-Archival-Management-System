"""Location entity schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    """Schema for POST /api/v1/locations."""

    authorized_name: str = Field(min_length=1, max_length=500)
    variant_names: str | None = Field(
        default=None,
        description="Pipe-delimited alternate names, e.g. 'Jones Mill|Jones's Mill'",
    )
    location_type_id: int | None = Field(
        default=None, description="vocabulary_terms ID from 'location_type' domain"
    )
    geo_latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    geo_longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    address: str | None = None
    description: str | None = None
    date_established: date | None = None
    date_ceased: date | None = None
    parent_location_id: int | None = None
    wikidata_qid: str | None = Field(default=None, max_length=20)
    is_public: bool = False
    public_description: str | None = None


class LocationUpdate(BaseModel):
    """Schema for PATCH /api/v1/locations/{id}. All fields optional."""

    authorized_name: str | None = Field(default=None, min_length=1, max_length=500)
    variant_names: str | None = None
    location_type_id: int | None = None
    geo_latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    geo_longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    address: str | None = None
    description: str | None = None
    date_established: date | None = None
    date_ceased: date | None = None
    parent_location_id: int | None = None
    wikidata_qid: str | None = Field(default=None, max_length=20)
    is_public: bool | None = None
    public_description: str | None = None


class LocationResponse(BaseModel):
    """Full location entity response."""

    id: int
    authorized_name: str
    variant_names: str | None = None
    location_type_id: int | None = None
    geo_latitude: Decimal | None = None
    geo_longitude: Decimal | None = None
    address: str | None = None
    description: str | None = None
    date_established: date | None = None
    date_ceased: date | None = None
    parent_location_id: int | None = None
    wikidata_qid: str | None = None
    is_public: bool = False
    public_description: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
