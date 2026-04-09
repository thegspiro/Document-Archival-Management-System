"""CSV import job tracking."""

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

IMPORT_MODE_ENUM = Enum("template", "mapped", name="import_mode")
IMPORT_STATUS_ENUM = Enum(
    "uploaded", "validating", "validation_failed", "ready",
    "importing", "complete", "failed",
    name="import_status",
)
IMPORT_ROW_STATUS_ENUM = Enum(
    "pending", "valid", "warning", "error", "imported", "skipped",
    name="import_row_status",
)


class CsvImport(Base, IDMixin, TimestampMixin):
    __tablename__ = "csv_imports"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    import_mode: Mapped[str] = mapped_column(IMPORT_MODE_ENUM, nullable=False)
    status: Mapped[str] = mapped_column(
        IMPORT_STATUS_ENUM, default="uploaded", nullable=False
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_node_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("arrangement_nodes.id"), nullable=True
    )
    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_vocabulary_terms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    rows: Mapped[list["CsvImportRow"]] = relationship(back_populates="csv_import")


class CsvImportRow(Base, IDMixin):
    __tablename__ = "csv_import_rows"

    import_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("csv_imports.id"), nullable=False
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    mapped_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        IMPORT_ROW_STATUS_ENUM, default="pending", nullable=False
    )
    messages: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    csv_import: Mapped["CsvImport"] = relationship(back_populates="rows")
