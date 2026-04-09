"""Immutable preservation event records (PREMIS / OAIS)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

PRESERVATION_EVENT_TYPE = Enum(
    "ingest", "fixity_check", "format_validation", "virus_scan",
    "ocr", "migration", "deletion", "access", "modification", "replication",
    name="preservation_event_type",
)
PRESERVATION_OUTCOME = Enum("success", "failure", "warning", name="preservation_outcome")


class PreservationEvent(Base, IDMixin):
    __tablename__ = "preservation_events"

    document_file_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("document_files.id"), nullable=True
    )
    document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(PRESERVATION_EVENT_TYPE, nullable=False)
    event_outcome: Mapped[str] = mapped_column(PRESERVATION_OUTCOME, nullable=False)
    event_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent: Mapped[str | None] = mapped_column(String(200), nullable=True)
    event_datetime: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
