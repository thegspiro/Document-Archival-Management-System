"""Review queue for documents needing human review."""

from sqlalchemy import BigInteger, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

REVIEW_REASON_ENUM = Enum(
    "llm_suggestions", "manual_flag", "import", "initial_review", "integrity_failure",
    name="review_reason",
)
REVIEW_PRIORITY_ENUM = Enum("low", "normal", "high", name="review_priority")


class ReviewQueue(Base, IDMixin, TimestampMixin):
    __tablename__ = "review_queue"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), unique=True, nullable=False
    )
    reason: Mapped[str] = mapped_column(REVIEW_REASON_ENUM, nullable=False)
    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    priority: Mapped[str] = mapped_column(REVIEW_PRIORITY_ENUM, default="normal", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
