"""Exhibition models — pages and blocks for public exhibits."""

from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin

BLOCK_TYPE_ENUM = Enum(
    "html", "file_with_text", "gallery", "document_metadata",
    "map", "timeline", "table_of_contents", "collection_browse", "separator",
    name="block_type",
)
BLOCK_LAYOUT_ENUM = Enum("full", "left", "right", "center", name="block_layout")


class Exhibition(Base, IDMixin, TimestampMixin):
    __tablename__ = "exhibitions"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    header_image_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    accent_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    show_summary_page: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    pages: Mapped[list["ExhibitionPage"]] = relationship(back_populates="exhibition", lazy="selectin")
    tags: Mapped[list["ExhibitionTag"]] = relationship(back_populates="exhibition", lazy="selectin")


class ExhibitionTag(Base, IDMixin):
    __tablename__ = "exhibition_tags"
    __table_args__ = (
        UniqueConstraint("exhibition_id", "term_id", name="uq_exhibition_tags"),
    )

    exhibition_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exhibitions.id"), nullable=False
    )
    term_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vocabulary_terms.id"), nullable=False
    )

    exhibition: Mapped["Exhibition"] = relationship(back_populates="tags")


class ExhibitionPage(Base, IDMixin, TimestampMixin):
    __tablename__ = "exhibition_pages"
    __table_args__ = (
        UniqueConstraint("exhibition_id", "slug", name="uq_exhibition_page_slug"),
    )

    exhibition_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exhibitions.id"), nullable=False
    )
    parent_page_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("exhibition_pages.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    menu_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exhibition: Mapped["Exhibition"] = relationship(back_populates="pages")
    blocks: Mapped[list["ExhibitionPageBlock"]] = relationship(
        back_populates="page", lazy="selectin"
    )


class ExhibitionPageBlock(Base, IDMixin, TimestampMixin):
    __tablename__ = "exhibition_page_blocks"

    page_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("exhibition_pages.id"), nullable=False
    )
    block_type: Mapped[str] = mapped_column(BLOCK_TYPE_ENUM, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    layout: Mapped[str] = mapped_column(BLOCK_LAYOUT_ENUM, default="full", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    page: Mapped["ExhibitionPage"] = relationship(back_populates="blocks")
