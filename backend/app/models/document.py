"""Document model — the core ISAD(G) item-level record."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Enum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

DESCRIPTION_STATUS_ENUM = Enum("draft", "revised", "final", name="description_status")
COPYRIGHT_STATUS_ENUM = Enum(
    "copyrighted", "public_domain", "unknown", "orphan_work", "creative_commons",
    name="copyright_status",
)
AVAILABILITY_STATUS_ENUM = Enum(
    "available", "temporarily_unavailable", "deaccessioned",
    name="availability_status",
)
TOMBSTONE_DISCLOSURE_ENUM = Enum(
    "none", "accession_only", "collection_and_accession",
    name="tombstone_disclosure",
)
COMPLETENESS_ENUM = Enum("none", "minimal", "standard", "full", name="description_completeness")
LEVEL_OF_DESCRIPTION_ENUM = Enum(
    "fonds", "subfonds", "series", "subseries", "file", "item",
    name="level_of_description",
)
REVIEW_STATUS_ENUM = Enum("none", "pending", "approved", "rejected", name="review_status")
INBOX_STATUS_ENUM = Enum("inbox", "processed", name="inbox_status")
DEACCESSION_STATUS_ENUM = Enum(
    "none", "proposed", "approved", "complete", name="deaccession_status"
)


class Document(Base, IDMixin, TimestampMixin):
    __tablename__ = "documents"

    arrangement_node_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("arrangement_nodes.id"), nullable=True
    )
    accession_number: Mapped[str | None] = mapped_column(
        String(200), unique=True, nullable=True
    )
    # Version group fields
    version_group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("document_version_groups.id"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    version_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_canonical_version: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ISAD(G) Identity Statement Area
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    reference_code: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date_display: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    level_of_description: Mapped[str] = mapped_column(
        LEVEL_OF_DESCRIPTION_ENUM, default="item", nullable=False
    )
    extent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ISAD(G) Context Area
    creator_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("authority_records.id"), nullable=True
    )
    administrative_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    archival_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    immediate_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ISAD(G) Content and Structure Area
    scope_and_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    appraisal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    accruals: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_of_arrangement: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ISAD(G) Conditions of Access Area
    access_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    reproduction_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    language_of_material: Mapped[str | None] = mapped_column(String(500), nullable=True)
    physical_characteristics: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding_aids: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ISAD(G) Allied Materials Area
    location_of_originals: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_of_copies: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_units: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ISAD(G) Notes Area
    general_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    archivists_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ISAD(G) Description Control Area
    rules_or_conventions: Mapped[str] = mapped_column(
        String(200), default="DACS", nullable=False
    )
    description_status: Mapped[str] = mapped_column(
        DESCRIPTION_STATUS_ENUM, default="draft", nullable=False
    )
    description_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    described_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Rights and Copyright
    copyright_status: Mapped[str] = mapped_column(
        COPYRIGHT_STATUS_ENUM, default="unknown", nullable=False
    )
    rights_holder: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rights_basis: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rights_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    embargo_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    donor_agreement_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("donor_agreements.id"), nullable=True
    )

    # Application fields
    document_type_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    physical_format_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    condition_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    original_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    scanned_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_title: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Tombstone and availability
    availability_status: Mapped[str] = mapped_column(
        AVAILABILITY_STATUS_ENUM, default="available", nullable=False
    )
    unavailable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    unavailable_since: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    unavailable_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    tombstone_disclosure: Mapped[str] = mapped_column(
        TOMBSTONE_DISCLOSURE_ENUM, default="accession_only", nullable=False
    )

    # Content advisory
    has_content_advisory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_advisory_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Description completeness
    description_completeness: Mapped[str] = mapped_column(
        COMPLETENESS_ENUM, default="none", nullable=False
    )
    description_completeness_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Geolocation
    geo_latitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    geo_longitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    geo_location_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Persistent identifier
    ark_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Workflow
    review_status: Mapped[str] = mapped_column(
        REVIEW_STATUS_ENUM, default="none", nullable=False
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    inbox_status: Mapped[str] = mapped_column(
        INBOX_STATUS_ENUM, default="inbox", nullable=False
    )
    deaccession_status: Mapped[str] = mapped_column(
        DEACCESSION_STATUS_ENUM, default="none", nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    arrangement_node: Mapped["ArrangementNode | None"] = relationship(lazy="selectin")
    creator: Mapped["AuthorityRecord | None"] = relationship(lazy="selectin")
    files: Mapped[list["DocumentFile"]] = relationship(
        back_populates="document", lazy="selectin"
    )
    terms: Mapped[list["DocumentTerm"]] = relationship(
        back_populates="document", lazy="selectin"
    )


# Avoid circular import issues — these are string references resolved at runtime
from app.models.arrangement import ArrangementNode  # noqa: E402
from app.models.authority_record import AuthorityRecord  # noqa: E402
from app.models.document_file import DocumentFile  # noqa: E402
from app.models.document_term import DocumentTerm  # noqa: E402
