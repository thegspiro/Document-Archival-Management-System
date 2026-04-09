"""Fixity check log (OAIS requirement)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

FIXITY_OUTCOME = Enum("match", "mismatch", "file_missing", name="fixity_outcome")


class FixityCheck(Base, IDMixin):
    __tablename__ = "fixity_checks"

    document_file_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("document_files.id"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
    stored_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    computed_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(FIXITY_OUTCOME, nullable=False)
    checked_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
