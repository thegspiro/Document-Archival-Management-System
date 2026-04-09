"""Document schemas — request and response models covering all ISAD(G) fields."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import PaginatedResponse


# ---------------------------------------------------------------------------
# Enums as Literal types for Pydantic validation
# ---------------------------------------------------------------------------

LevelOfDescription = Literal[
    "fonds", "subfonds", "series", "subseries", "file", "item"
]
DescriptionStatus = Literal["draft", "revised", "final"]
CopyrightStatus = Literal[
    "copyrighted", "public_domain", "unknown", "orphan_work", "creative_commons"
]
AvailabilityStatus = Literal["available", "temporarily_unavailable", "deaccessioned"]
TombstoneDisclosure = Literal["none", "accession_only", "collection_and_accession"]
DescriptionCompleteness = Literal["none", "minimal", "standard", "full"]
ReviewStatus = Literal["none", "pending", "approved", "rejected"]
InboxStatus = Literal["inbox", "processed"]
DeaccessionStatus = Literal["none", "proposed", "approved", "complete"]


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class DocumentCreate(BaseModel):
    """Schema for POST /api/v1/documents.

    Only ``title`` is required; every other field is optional on initial creation
    so that watch-folder ingest and quick-add workflows can create stub records.
    """

    arrangement_node_id: int | None = None
    accession_number: str | None = Field(
        default=None,
        max_length=200,
        description="Leave blank for auto-assignment",
    )

    # ISAD(G) Identity Statement Area
    title: str = Field(min_length=1, max_length=1000)
    reference_code: str | None = Field(default=None, max_length=200)
    date_display: str | None = Field(default=None, max_length=200)
    date_start: date | None = None
    date_end: date | None = None
    level_of_description: LevelOfDescription = "item"
    extent: str | None = Field(default=None, max_length=500)

    # ISAD(G) Context Area
    creator_id: int | None = None
    administrative_history: str | None = None
    archival_history: str | None = None
    immediate_source: str | None = None

    # ISAD(G) Content and Structure Area
    scope_and_content: str | None = None
    appraisal_notes: str | None = None
    accruals: str | None = None
    system_of_arrangement: str | None = None

    # ISAD(G) Conditions of Access Area
    access_conditions: str | None = None
    reproduction_conditions: str | None = None
    language_of_material: str | None = Field(default=None, max_length=500)
    physical_characteristics: str | None = None
    finding_aids: str | None = None

    # ISAD(G) Allied Materials Area
    location_of_originals: str | None = None
    location_of_copies: str | None = None
    related_units: str | None = None
    publication_note: str | None = None

    # ISAD(G) Notes Area
    general_note: str | None = None
    archivists_note: str | None = None

    # ISAD(G) Description Control Area
    rules_or_conventions: str = Field(default="DACS", max_length=200)
    description_status: DescriptionStatus = "draft"
    description_date: date | None = None
    described_by: int | None = None

    # Rights and Copyright
    copyright_status: CopyrightStatus = "unknown"
    rights_holder: str | None = Field(default=None, max_length=500)
    rights_basis: str | None = Field(default=None, max_length=200)
    rights_note: str | None = None
    embargo_end_date: date | None = None
    donor_agreement_id: int | None = None

    # Application fields
    document_type_id: int | None = None
    physical_format_id: int | None = None
    condition_id: int | None = None
    original_location: str | None = None
    scan_date: date | None = None
    is_public: bool = False
    public_title: str | None = Field(default=None, max_length=1000)

    # Geolocation
    geo_latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    geo_longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    geo_location_name: str | None = Field(default=None, max_length=500)

    # Content advisory
    has_content_advisory: bool = False
    content_advisory_note: str | None = None

    @field_validator("date_end")
    @classmethod
    def date_end_after_start(cls, v: date | None, info: Any) -> date | None:
        """Ensure date_end is not before date_start when both are provided."""
        date_start = info.data.get("date_start")
        if v is not None and date_start is not None and v < date_start:
            raise ValueError("date_end must not be before date_start")
        return v


class DocumentUpdate(BaseModel):
    """Schema for PATCH /api/v1/documents/{id}. All fields are optional."""

    arrangement_node_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=1000)
    reference_code: str | None = Field(default=None, max_length=200)
    date_display: str | None = Field(default=None, max_length=200)
    date_start: date | None = None
    date_end: date | None = None
    level_of_description: LevelOfDescription | None = None
    extent: str | None = Field(default=None, max_length=500)

    # Context Area
    creator_id: int | None = None
    administrative_history: str | None = None
    archival_history: str | None = None
    immediate_source: str | None = None

    # Content and Structure Area
    scope_and_content: str | None = None
    appraisal_notes: str | None = None
    accruals: str | None = None
    system_of_arrangement: str | None = None

    # Conditions of Access Area
    access_conditions: str | None = None
    reproduction_conditions: str | None = None
    language_of_material: str | None = Field(default=None, max_length=500)
    physical_characteristics: str | None = None
    finding_aids: str | None = None

    # Allied Materials Area
    location_of_originals: str | None = None
    location_of_copies: str | None = None
    related_units: str | None = None
    publication_note: str | None = None

    # Notes Area
    general_note: str | None = None
    archivists_note: str | None = None

    # Description Control Area
    rules_or_conventions: str | None = Field(default=None, max_length=200)
    description_status: DescriptionStatus | None = None
    description_date: date | None = None
    described_by: int | None = None

    # Rights and Copyright
    copyright_status: CopyrightStatus | None = None
    rights_holder: str | None = Field(default=None, max_length=500)
    rights_basis: str | None = Field(default=None, max_length=200)
    rights_note: str | None = None
    embargo_end_date: date | None = None
    donor_agreement_id: int | None = None

    # Application fields
    document_type_id: int | None = None
    physical_format_id: int | None = None
    condition_id: int | None = None
    original_location: str | None = None
    scan_date: date | None = None
    is_public: bool | None = None
    public_title: str | None = Field(default=None, max_length=1000)

    # Geolocation
    geo_latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    geo_longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    geo_location_name: str | None = Field(default=None, max_length=500)

    # Content advisory
    has_content_advisory: bool | None = None
    content_advisory_note: str | None = None

    # Workflow overrides — normally managed by services but settable by admins
    review_status: ReviewStatus | None = None
    review_notes: str | None = None
    inbox_status: InboxStatus | None = None

    @field_validator("date_end")
    @classmethod
    def date_end_after_start(cls, v: date | None, info: Any) -> date | None:
        date_start = info.data.get("date_start")
        if v is not None and date_start is not None and v < date_start:
            raise ValueError("date_end must not be before date_start")
        return v


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class DocumentResponse(BaseModel):
    """Full document response including all ISAD(G) fields, versioning, and workflow state."""

    id: int
    arrangement_node_id: int | None = None
    accession_number: str | None = None

    # Version group
    version_group_id: int | None = None
    version_number: int = 1
    version_label: str | None = None
    is_canonical_version: bool = False

    # ISAD(G) Identity Statement Area
    title: str
    reference_code: str | None = None
    date_display: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    level_of_description: LevelOfDescription = "item"
    extent: str | None = None

    # ISAD(G) Context Area
    creator_id: int | None = None
    administrative_history: str | None = None
    archival_history: str | None = None
    immediate_source: str | None = None

    # ISAD(G) Content and Structure Area
    scope_and_content: str | None = None
    appraisal_notes: str | None = None
    accruals: str | None = None
    system_of_arrangement: str | None = None

    # ISAD(G) Conditions of Access Area
    access_conditions: str | None = None
    reproduction_conditions: str | None = None
    language_of_material: str | None = None
    physical_characteristics: str | None = None
    finding_aids: str | None = None

    # ISAD(G) Allied Materials Area
    location_of_originals: str | None = None
    location_of_copies: str | None = None
    related_units: str | None = None
    publication_note: str | None = None

    # ISAD(G) Notes Area
    general_note: str | None = None
    archivists_note: str | None = None

    # ISAD(G) Description Control Area
    rules_or_conventions: str = "DACS"
    description_status: DescriptionStatus = "draft"
    description_date: date | None = None
    described_by: int | None = None

    # Rights and Copyright
    copyright_status: CopyrightStatus = "unknown"
    rights_holder: str | None = None
    rights_basis: str | None = None
    rights_note: str | None = None
    embargo_end_date: date | None = None
    donor_agreement_id: int | None = None

    # Application fields
    document_type_id: int | None = None
    physical_format_id: int | None = None
    condition_id: int | None = None
    original_location: str | None = None
    scan_date: date | None = None
    scanned_by: int | None = None
    is_public: bool = False
    public_title: str | None = None

    # Tombstone and availability
    availability_status: AvailabilityStatus = "available"
    unavailable_reason: str | None = None
    unavailable_since: datetime | None = None
    unavailable_until: date | None = None
    tombstone_disclosure: TombstoneDisclosure = "accession_only"

    # Content advisory
    has_content_advisory: bool = False
    content_advisory_note: str | None = None

    # Description completeness
    description_completeness: DescriptionCompleteness = "none"
    description_completeness_updated_at: datetime | None = None

    # Geolocation
    geo_latitude: Decimal | None = None
    geo_longitude: Decimal | None = None
    geo_location_name: str | None = None

    # Persistent identifier
    ark_id: str | None = None

    # Workflow
    review_status: ReviewStatus = "none"
    review_notes: str | None = None
    llm_suggestions: dict[str, Any] | None = None
    inbox_status: InboxStatus = "inbox"
    deaccession_status: DeaccessionStatus = "none"

    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(PaginatedResponse["DocumentResponse"]):
    """Paginated list of documents."""

    pass


class MakeUnavailableRequest(BaseModel):
    """Request body for POST /api/v1/documents/{id}/make-unavailable."""

    reason: str = Field(min_length=1, description="Why the document is being pulled")
    unavailable_until: date | None = None
    tombstone_disclosure: TombstoneDisclosure = "accession_only"
