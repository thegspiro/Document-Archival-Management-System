"""Arrangement service — CRUD for the ISAD(G) hierarchical node tree."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arrangement import ArrangementNode
from app.models.document import Document
from app.services.audit_service import AuditService


class ArrangementService:
    """Business logic for the hierarchical arrangement (fonds/series/file) tree."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_node(
        db: AsyncSession,
        *,
        data: dict[str, Any],
        created_by: int | None = None,
        ip_address: str | None = None,
    ) -> ArrangementNode:
        """Create a new arrangement node."""
        data.setdefault("created_by", created_by)
        node = ArrangementNode(**data)
        db.add(node)
        await db.flush()

        await AuditService.log(
            db,
            user_id=created_by,
            action="arrangement_node.create",
            resource_type="arrangement_node",
            resource_id=node.id,
            detail={"title": node.title, "level_type": node.level_type},
            ip_address=ip_address,
        )
        return node

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    async def get_node(db: AsyncSession, *, node_id: int) -> ArrangementNode:
        """Return a single node by ID, or raise 404."""
        result = await db.execute(
            select(ArrangementNode).where(ArrangementNode.id == node_id)
        )
        node = result.scalar_one_or_none()
        if node is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arrangement node not found",
            )
        return node

    @staticmethod
    async def get_tree(
        db: AsyncSession,
        *,
        root_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return the full node tree (or a subtree rooted at *root_id*)
        as a nested list of dicts.

        Each dict has keys: ``id``, ``title``, ``level_type``, ``identifier``,
        ``is_public``, ``sort_order``, ``children``.
        """
        if root_id is not None:
            query = select(ArrangementNode).where(ArrangementNode.id == root_id)
        else:
            query = select(ArrangementNode).where(ArrangementNode.parent_id.is_(None))

        result = await db.execute(query.order_by(ArrangementNode.sort_order))
        roots = list(result.scalars().all())

        async def _build(node: ArrangementNode) -> dict[str, Any]:
            child_result = await db.execute(
                select(ArrangementNode)
                .where(ArrangementNode.parent_id == node.id)
                .order_by(ArrangementNode.sort_order)
            )
            children = list(child_result.scalars().all())
            return {
                "id": node.id,
                "title": node.title,
                "level_type": node.level_type,
                "identifier": node.identifier,
                "is_public": node.is_public,
                "sort_order": node.sort_order,
                "children": [await _build(c) for c in children],
            }

        return [await _build(r) for r in roots]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_node(
        db: AsyncSession,
        *,
        node_id: int,
        data: dict[str, Any],
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> ArrangementNode:
        """Patch mutable fields on an arrangement node."""
        node = await ArrangementService.get_node(db, node_id=node_id)

        protected = {"id", "created_at", "updated_at", "created_by"}
        changes: dict[str, Any] = {}
        for key, value in data.items():
            if key in protected:
                continue
            if hasattr(node, key):
                setattr(node, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="arrangement_node.update",
            resource_type="arrangement_node",
            resource_id=node.id,
            detail=changes,
            ip_address=ip_address,
        )
        return node

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_node(
        db: AsyncSession,
        *,
        node_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Delete an arrangement node.

        Raises 400 if the node has child nodes or attached documents.
        """
        node = await ArrangementService.get_node(db, node_id=node_id)

        # Guard: children
        child_result = await db.execute(
            select(func.count(ArrangementNode.id)).where(
                ArrangementNode.parent_id == node_id
            )
        )
        if child_result.scalar_one() > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a node that has child nodes",
            )

        # Guard: documents
        doc_result = await db.execute(
            select(func.count(Document.id)).where(
                Document.arrangement_node_id == node_id
            )
        )
        if doc_result.scalar_one() > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a node that has documents attached",
            )

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="arrangement_node.delete",
            resource_type="arrangement_node",
            resource_id=node.id,
            detail={"title": node.title},
            ip_address=ip_address,
        )

        await db.delete(node)
        await db.flush()

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    @staticmethod
    async def get_node_documents(
        db: AsyncSession,
        *,
        node_id: int,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return paginated documents attached to this node (canonical only)."""
        query = select(Document).where(
            Document.arrangement_node_id == node_id,
            or_(
                Document.version_group_id.is_(None),
                Document.is_canonical_version.is_(True),
            ),
        )

        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            query.order_by(Document.sort_order if hasattr(Document, "sort_order") else Document.id)
            .offset(offset)
            .limit(per_page)
        )
        items = list(result.scalars().all())
        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}
