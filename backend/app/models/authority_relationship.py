"""Authority record relationships (person-to-person, org-to-org, etc.)."""

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class AuthorityRelationship(Base, IDMixin, TimestampMixin):
    __tablename__ = "authority_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_authority_id", "target_authority_id", "relationship_type_id",
            name="uq_authority_relationships",
        ),
    )

    source_authority_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("authority_records.id"), nullable=False
    )
    target_authority_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("authority_records.id"), nullable=False
    )
    relationship_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=False
    )
    date_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
