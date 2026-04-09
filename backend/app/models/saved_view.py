"""Saved views — personal dashboard filter presets."""

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

DISPLAY_TYPE_ENUM = Enum("count", "list", "grid", name="saved_view_display")


class SavedView(Base, IDMixin, TimestampMixin):
    __tablename__ = "saved_views"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    filter_params: Mapped[dict] = mapped_column(JSON, nullable=False)
    display_type: Mapped[str] = mapped_column(DISPLAY_TYPE_ENUM, default="list", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
