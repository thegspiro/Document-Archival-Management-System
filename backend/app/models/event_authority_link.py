"""Event-to-authority record links."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin


class EventAuthorityLink(Base, IDMixin):
    __tablename__ = "event_authority_links"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "authority_id", "role_id",
            name="uq_event_authority_links",
        ),
    )

    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=False)
    authority_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("authority_records.id"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
