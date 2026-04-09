"""Hierarchical arrangement nodes (ISAD(G) levels)."""

from sqlalchemy import BigInteger, Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

LEVEL_TYPE_ENUM = Enum(
    "fonds", "subfonds", "series", "subseries", "file", "item",
    name="arrangement_level_type",
)


class ArrangementNode(Base, IDMixin, TimestampMixin):
    __tablename__ = "arrangement_nodes"

    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("arrangement_nodes.id"), nullable=True
    )
    level_type: Mapped[str] = mapped_column(LEVEL_TYPE_ENUM, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_start: Mapped[str | None] = mapped_column(Date, nullable=True)
    date_end: Mapped[str | None] = mapped_column(Date, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    has_content_advisory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_advisory_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    parent: Mapped["ArrangementNode | None"] = relationship(
        remote_side="ArrangementNode.id", lazy="selectin"
    )
    children: Mapped[list["ArrangementNode"]] = relationship(lazy="selectin")
