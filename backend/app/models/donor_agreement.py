"""Donor agreements (AASLH requirement)."""

from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

AGREEMENT_TYPE_ENUM = Enum(
    "deed_of_gift", "deposit", "loan", "purchase", "transfer",
    name="agreement_type",
)


class DonorAgreement(Base, IDMixin, TimestampMixin):
    __tablename__ = "donor_agreements"

    donor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("authority_records.id"), nullable=False
    )
    agreement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    agreement_type: Mapped[str] = mapped_column(AGREEMENT_TYPE_ENUM, nullable=False)
    restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)
    embargo_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    allows_reproduction: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allows_publication: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    physical_items_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agreement_document_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
