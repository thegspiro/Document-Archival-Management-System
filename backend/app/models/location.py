"""Location entities — controlled place records."""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class Location(Base, IDMixin, TimestampMixin):
    __tablename__ = "locations"

    authorized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    variant_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_type_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    geo_latitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    geo_longitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_established: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_ceased: Mapped[date | None] = mapped_column(Date, nullable=True)
    parent_location_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("locations.id"), nullable=True
    )
    wikidata_qid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
