"""Exhibition service — CRUD for exhibitions, pages, and blocks with reordering."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exhibition import (
    Exhibition,
    ExhibitionPage,
    ExhibitionPageBlock,
    ExhibitionTag,
)
from app.services.audit_service import AuditService


class ExhibitionService:
    """Business logic for the public exhibition builder (pages and blocks)."""

    # ------------------------------------------------------------------
    # Exhibitions
    # ------------------------------------------------------------------

    @staticmethod
    async def create_exhibition(
        db: AsyncSession,
        *,
        data: dict[str, Any],
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> Exhibition:
        """Create a new exhibition."""
        data.setdefault("created_by", created_by)
        exhibition = Exhibition(**data)
        db.add(exhibition)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="exhibition.create",
            resource_type="exhibition",
            resource_id=exhibition.id,
            detail={"title": exhibition.title, "slug": exhibition.slug},
            ip_address=ip_address,
        )
        return exhibition

    @staticmethod
    async def get_exhibition(db: AsyncSession, *, exhibition_id: int) -> Exhibition:
        """Return an exhibition by ID, or raise 404."""
        result = await db.execute(
            select(Exhibition).where(Exhibition.id == exhibition_id)
        )
        exhibition = result.scalar_one_or_none()
        if exhibition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition not found",
            )
        return exhibition

    @staticmethod
    async def list_exhibitions(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
        published_only: bool = False,
    ) -> dict:
        """Return a paginated list of exhibitions."""
        query = select(Exhibition)
        if published_only:
            query = query.where(Exhibition.is_published.is_(True))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Exhibition.sort_order, Exhibition.id).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    @staticmethod
    async def update_exhibition(
        db: AsyncSession,
        *,
        exhibition_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> Exhibition:
        """Update mutable fields on an exhibition."""
        exhibition = await ExhibitionService.get_exhibition(db, exhibition_id=exhibition_id)

        protected = {"id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(exhibition, key):
                # Track publish transition.
                if key == "is_published" and value and not exhibition.is_published:
                    exhibition.published_at = datetime.now(tz=timezone.utc)
                setattr(exhibition, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition.update",
            resource_type="exhibition",
            resource_id=exhibition.id,
            detail=changes,
            ip_address=ip_address,
        )
        return exhibition

    @staticmethod
    async def delete_exhibition(
        db: AsyncSession,
        *,
        exhibition_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an exhibition and all its pages and blocks."""
        exhibition = await ExhibitionService.get_exhibition(db, exhibition_id=exhibition_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition.delete",
            resource_type="exhibition",
            resource_id=exhibition.id,
            detail={"title": exhibition.title},
            ip_address=ip_address,
        )
        await db.delete(exhibition)
        await db.flush()

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    @staticmethod
    async def create_page(
        db: AsyncSession,
        *,
        exhibition_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ExhibitionPage:
        """Create a new page within an exhibition."""
        # Verify exhibition exists.
        await ExhibitionService.get_exhibition(db, exhibition_id=exhibition_id)

        data["exhibition_id"] = exhibition_id
        page = ExhibitionPage(**data)
        db.add(page)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_page.create",
            resource_type="exhibition_page",
            resource_id=page.id,
            detail={"exhibition_id": exhibition_id, "title": page.title, "slug": page.slug},
            ip_address=ip_address,
        )
        return page

    @staticmethod
    async def get_page(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
    ) -> ExhibitionPage:
        """Return a specific page, or raise 404."""
        result = await db.execute(
            select(ExhibitionPage).where(
                ExhibitionPage.id == page_id,
                ExhibitionPage.exhibition_id == exhibition_id,
            )
        )
        page = result.scalar_one_or_none()
        if page is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition page not found",
            )
        return page

    @staticmethod
    async def list_pages(
        db: AsyncSession,
        *,
        exhibition_id: int,
    ) -> list[ExhibitionPage]:
        """Return all pages for an exhibition, ordered by sort_order."""
        result = await db.execute(
            select(ExhibitionPage)
            .where(ExhibitionPage.exhibition_id == exhibition_id)
            .order_by(ExhibitionPage.sort_order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_page(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ExhibitionPage:
        """Update mutable fields on an exhibition page."""
        page = await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        protected = {"id", "exhibition_id", "created_at", "updated_at"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(page, key):
                setattr(page, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_page.update",
            resource_type="exhibition_page",
            resource_id=page.id,
            detail=changes,
            ip_address=ip_address,
        )
        return page

    @staticmethod
    async def delete_page(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an exhibition page and all its blocks."""
        page = await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_page.delete",
            resource_type="exhibition_page",
            resource_id=page.id,
            detail={"title": page.title},
            ip_address=ip_address,
        )
        await db.delete(page)
        await db.flush()

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    @staticmethod
    async def create_block(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ExhibitionPageBlock:
        """Create a new content block on a page."""
        # Verify page belongs to exhibition.
        await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        data["page_id"] = page_id
        block = ExhibitionPageBlock(**data)
        db.add(block)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_block.create",
            resource_type="exhibition_page_block",
            resource_id=block.id,
            detail={"page_id": page_id, "block_type": block.block_type},
            ip_address=ip_address,
        )
        return block

    @staticmethod
    async def update_block(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        block_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ExhibitionPageBlock:
        """Update a content block."""
        # Verify hierarchy.
        await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        result = await db.execute(
            select(ExhibitionPageBlock).where(
                ExhibitionPageBlock.id == block_id,
                ExhibitionPageBlock.page_id == page_id,
            )
        )
        block = result.scalar_one_or_none()
        if block is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition block not found",
            )

        protected = {"id", "page_id", "created_at", "updated_at"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(block, key):
                setattr(block, key, value)
                changes[key] = str(value)[:200]  # Truncate large JSON in audit detail

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_block.update",
            resource_type="exhibition_page_block",
            resource_id=block.id,
            detail=changes,
            ip_address=ip_address,
        )
        return block

    @staticmethod
    async def delete_block(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        block_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete a content block."""
        await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        result = await db.execute(
            select(ExhibitionPageBlock).where(
                ExhibitionPageBlock.id == block_id,
                ExhibitionPageBlock.page_id == page_id,
            )
        )
        block = result.scalar_one_or_none()
        if block is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exhibition block not found",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_block.delete",
            resource_type="exhibition_page_block",
            resource_id=block.id,
            detail={"block_type": block.block_type},
            ip_address=ip_address,
        )
        await db.delete(block)
        await db.flush()

    # ------------------------------------------------------------------
    # Block reordering
    # ------------------------------------------------------------------

    @staticmethod
    async def reorder_blocks(
        db: AsyncSession,
        *,
        exhibition_id: int,
        page_id: int,
        block_ids: list[int],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Set the sort_order of blocks on a page according to the provided
        ordered list of block IDs.

        This is the non-drag alternative required by WCAG 2.5.7.
        """
        await ExhibitionService.get_page(db, exhibition_id=exhibition_id, page_id=page_id)

        for index, bid in enumerate(block_ids):
            await db.execute(
                update(ExhibitionPageBlock)
                .where(
                    ExhibitionPageBlock.id == bid,
                    ExhibitionPageBlock.page_id == page_id,
                )
                .values(sort_order=index)
            )
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="exhibition_block.reorder",
            resource_type="exhibition_page",
            resource_id=page_id,
            detail={"new_order": block_ids},
            ip_address=ip_address,
        )
