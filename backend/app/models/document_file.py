"""Document files — physical files attached to a document record."""

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

OCR_STATUS_ENUM = Enum(
    "none", "queued", "processing", "complete", "failed", name="ocr_status"
)
IMAGE_QUALITY_ENUM = Enum(
    "preservation_master", "production_master", "access_copy", "unknown",
    name="image_quality_rating",
)


class DocumentFile(Base, IDMixin, TimestampMixin):
    __tablename__ = "document_files"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(2000), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # OCR
    ocr_status: Mapped[str] = mapped_column(OCR_STATUS_ENUM, default="none", nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ocr_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Technical metadata
    scan_resolution_ppi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bit_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color_space: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scanner_make: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scanner_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scanning_software: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_quality_rating: Mapped[str] = mapped_column(
        IMAGE_QUALITY_ENUM, default="unknown", nullable=False
    )

    # Format characterization (PREMIS / OAIS)
    format_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    format_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    format_puid: Mapped[str | None] = mapped_column(String(50), nullable=True)
    format_registry: Mapped[str] = mapped_column(String(50), default="PRONOM", nullable=False)
    format_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    format_validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    preservation_warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="files")
    pages: Mapped[list["DocumentPage"]] = relationship(back_populates="document_file", lazy="selectin")


from app.models.document import Document  # noqa: E402
from app.models.document_page import DocumentPage  # noqa: E402
