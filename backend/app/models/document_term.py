"""Document-term junction table (tags, categories, etc.)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin


class DocumentTerm(Base, IDMixin):
    __tablename__ = "document_terms"
    __table_args__ = (
        UniqueConstraint("document_id", "term_id", name="uq_document_terms"),
    )

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
    term_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=False
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default="CURRENT_TIMESTAMP", nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="terms")
    term: Mapped["VocabularyTerm"] = relationship(lazy="selectin")


from app.models.document import Document  # noqa: E402
from app.models.vocabulary import VocabularyTerm  # noqa: E402
