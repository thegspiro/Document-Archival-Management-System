"""Deaccession log (AASLH requirement) — immutable."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

DISPOSITION_ENUM = Enum(
    "destroyed", "transferred", "returned", "sold", "donated",
    name="deaccession_disposition",
)


class DeaccessionLog(Base, IDMixin):
    __tablename__ = "deaccession_log"

    document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    accession_number: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    deaccession_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    reason_note: Mapped[str] = mapped_column(Text, nullable=False)
    disposition: Mapped[str] = mapped_column(DISPOSITION_ENUM, nullable=False)
    transfer_destination: Mapped[str | None] = mapped_column(Text, nullable=True)
    authorized_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
