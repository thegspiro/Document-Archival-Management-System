"""Document-to-location links."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

LINK_TYPE_ENUM = Enum(
    "mentioned", "depicted", "created_at", "event_location",
    name="doc_location_link_type",
)


class DocumentLocationLink(Base, IDMixin):
    __tablename__ = "document_location_links"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "location_id", "link_type",
            name="uq_document_location_links",
        ),
    )

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
    location_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("locations.id"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(LINK_TYPE_ENUM, default="mentioned", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
