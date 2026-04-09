"""Sequences for atomic accession number generation."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin


class Sequence(Base, IDMixin):
    __tablename__ = "sequences"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    current_value: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
