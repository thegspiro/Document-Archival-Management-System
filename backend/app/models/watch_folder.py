"""Watch folders for automated file ingest."""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin


class WatchFolder(Base, IDMixin, TimestampMixin):
    __tablename__ = "watch_folders"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str] = mapped_column(String(2000), nullable=False)
    target_node_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("arrangement_nodes.id"), nullable=True
    )
    default_tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
