"""Document annotations — region and text range notes on pages."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

ANNOTATION_TYPE_ENUM = Enum("region", "text_range", name="annotation_type")


class DocumentAnnotation(Base, IDMixin, TimestampMixin):
    __tablename__ = "document_annotations"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
    document_file_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("document_files.id"), nullable=False
    )
    document_page_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("document_pages.id"), nullable=True
    )
    annotation_type: Mapped[str] = mapped_column(ANNOTATION_TYPE_ENUM, nullable=False)
    region_geometry: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    text_range: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
