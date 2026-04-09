"""Arrangement nodes router — the archival hierarchy (Fonds -> ... -> Item).

Supports tree and flat listing, CRUD, sub-tree documents, permissions,
collection-level export and citation.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class NodeCreate(BaseModel):
    parent_id: int | None = None
    level_type: str = Field(description="fonds|subfonds|series|subseries|file|item")
    title: str = Field(min_length=1, max_length=500)
    identifier: str | None = None
    description: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    is_public: bool = False
    sort_order: int = 0


class NodeUpdate(BaseModel):
    parent_id: int | None = None
    level_type: str | None = None
    title: str | None = None
    identifier: str | None = None
    description: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    is_public: bool | None = None
    sort_order: int | None = None


class NodeOut(BaseModel):
    id: int
    parent_id: int | None = None
    level_type: str
    title: str
    identifier: str | None = None
    description: str | None = None
    is_public: bool
    sort_order: int
    children: list["NodeOut"] = []

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    user_id: int | None = None
    role_id: int | None = None
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_manage_permissions: bool = False


class PermissionOut(BaseModel):
    id: int
    arrangement_node_id: int
    user_id: int | None = None
    role_id: int | None = None
    can_view: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
    can_manage_permissions: bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[NodeOut])
async def list_nodes(
    flat: bool = Query(False, description="Return flat list instead of tree"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the arrangement hierarchy as a tree or flat list."""
    from app.services import node_service

    return await node_service.list_nodes(db, flat=flat, user=current_user)


@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
async def create_node(
    body: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin", "archivist")),
) -> Any:
    """Create a new arrangement node."""
    from app.services import node_service

    return await node_service.create_node(db, body, current_user)


@router.get("/{node_id}", response_model=NodeOut)
async def get_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single arrangement node by ID."""
    from app.services import node_service

    node = await node_service.get_node(db, node_id, current_user)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return node


@router.patch("/{node_id}", response_model=NodeOut)
async def update_node(
    node_id: int,
    body: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin", "archivist")),
) -> Any:
    """Update an arrangement node."""
    from app.services import node_service

    node = await node_service.update_node(db, node_id, body, current_user)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete an arrangement node. Must be empty (no child nodes or documents)."""
    from app.services import node_service

    success = await node_service.delete_node(db, node_id, current_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")


@router.get("/{node_id}/documents", response_model=PaginatedResponse[Any])
async def list_node_documents(
    node_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List documents within an arrangement node's subtree."""
    from app.services import node_service

    return await node_service.list_node_documents(
        db, node_id, page=page, per_page=per_page, user=current_user
    )


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


@router.get("/{node_id}/permissions", response_model=list[PermissionOut])
async def list_permissions(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """List collection-level permissions for a node."""
    from app.services import permission_service

    return await permission_service.list_permissions(db, node_id)


@router.post(
    "/{node_id}/permissions",
    response_model=PermissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_permission(
    node_id: int,
    body: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> Any:
    """Grant a permission on an arrangement node."""
    from app.services import permission_service

    return await permission_service.create_permission(db, node_id, body, current_user)


@router.delete("/{node_id}/permissions/{perm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    node_id: int,
    perm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Revoke a specific permission grant."""
    from app.services import permission_service

    success = await permission_service.delete_permission(db, node_id, perm_id, current_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")


# ---------------------------------------------------------------------------
# Export and Citation
# ---------------------------------------------------------------------------


@router.get("/{node_id}/export")
async def export_node(
    node_id: int,
    format: str = Query(..., description="ead3 | csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Export a collection subtree as EAD3 XML or CSV."""
    from app.services import export_service

    content, media_type, filename = await export_service.export_node(
        db, node_id, format, current_user
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{node_id}/cite")
async def cite_node(
    node_id: int,
    format: str = Query("chicago_note", description="Citation format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate an archival collection-level citation."""
    from app.services import citation_service

    result = await citation_service.cite_node(db, node_id, format)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return result
