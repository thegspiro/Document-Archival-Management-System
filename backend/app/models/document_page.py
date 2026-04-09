"""Document pages — individual pages within a document file."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class DocumentPage(Base, IDMixin, TimestampMixin):
    __tablename__ = "document_pages"

    document_file_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("document_files.id"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    document_file: Mapped["DocumentFile"] = relationship(back_populates="pages")


from app.models.document_file import DocumentFile  # noqa: E402
