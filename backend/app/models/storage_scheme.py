"""Storage scheme configuration."""

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

SCHEME_TYPE_ENUM = Enum(
    "location", "donor", "subject", "date", "record_number",
    name="storage_scheme_type",
)


class StorageScheme(Base, IDMixin, TimestampMixin):
    __tablename__ = "storage_schemes"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scheme_type: Mapped[str] = mapped_column(SCHEME_TYPE_ENUM, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
