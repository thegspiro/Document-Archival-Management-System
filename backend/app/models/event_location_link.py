"""Event-to-location links."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

EVENT_LOC_LINK_TYPE = Enum(
    "primary", "secondary", "mentioned", name="event_loc_link_type"
)


class EventLocationLink(Base, IDMixin):
    __tablename__ = "event_location_links"
    __table_args__ = (
        UniqueConstraint("event_id", "location_id", name="uq_event_location_links"),
    )

    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("events.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("locations.id"), nullable=False
    )
    link_type: Mapped[str] = mapped_column(
        EVENT_LOC_LINK_TYPE, default="primary", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
