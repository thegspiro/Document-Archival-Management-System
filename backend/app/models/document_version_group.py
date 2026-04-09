"""Document version groups."""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class DocumentVersionGroup(Base, IDMixin, TimestampMixin):
    __tablename__ = "document_version_groups"

    base_accession_number: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    canonical_document_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    public_document_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
