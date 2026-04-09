"""Controlled vocabulary domains and terms."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class VocabularyDomain(Base, IDMixin, TimestampMixin):
    __tablename__ = "vocabulary_domains"

    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    allows_user_addition: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    terms: Mapped[list["VocabularyTerm"]] = relationship(back_populates="domain", lazy="selectin")


class VocabularyTerm(Base, IDMixin, TimestampMixin):
    __tablename__ = "vocabulary_terms"

    domain_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vocabulary_domains.id"), nullable=False
    )
    term: Mapped[str] = mapped_column(String(500), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    broader_term_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    domain: Mapped["VocabularyDomain"] = relationship(back_populates="terms")
