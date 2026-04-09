"""Event-to-document links."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

EVENT_DOC_LINK_TYPE = Enum(
    "produced_by", "about", "referenced_in", "precedes", "follows",
    name="event_doc_link_type",
)


class EventDocumentLink(Base, IDMixin):
    __tablename__ = "event_document_links"
    __table_args__ = (
        UniqueConstraint("event_id", "document_id", name="uq_event_document_links"),
    )

    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(EVENT_DOC_LINK_TYPE, default="about", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
