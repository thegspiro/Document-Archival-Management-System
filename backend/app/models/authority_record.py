"""Authority records — persons, organizations, families."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

ENTITY_TYPE_ENUM = Enum("person", "organization", "family", name="entity_type")


class AuthorityRecord(Base, IDMixin, TimestampMixin):
    __tablename__ = "authority_records"

    entity_type: Mapped[str] = mapped_column(ENTITY_TYPE_ENUM, nullable=False)
    authorized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    variant_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    dates: Mapped[str | None] = mapped_column(String(200), nullable=True)
    biographical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    administrative_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Wikidata
    wikidata_qid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    wikidata_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wikidata_enrichment: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # NER provenance
    created_by_ner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
