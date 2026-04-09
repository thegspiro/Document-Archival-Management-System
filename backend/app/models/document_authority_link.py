"""Document-to-authority record links (non-creator roles)."""

from sqlalchemy import BigInteger, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class DocumentAuthorityLink(Base, IDMixin, TimestampMixin):
    __tablename__ = "document_authority_links"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "authority_id", "role_id",
            name="uq_document_authority_links",
        ),
    )

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
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
