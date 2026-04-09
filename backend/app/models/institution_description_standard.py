"""Institution description standards for completeness levels."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin

COMPLETENESS_LEVEL_ENUM = Enum("minimal", "standard", "full", name="completeness_level")


class InstitutionDescriptionStandard(Base, IDMixin):
    __tablename__ = "institution_description_standards"

    level: Mapped[str] = mapped_column(COMPLETENESS_LEVEL_ENUM, nullable=False)
    required_fields: Mapped[dict] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )
