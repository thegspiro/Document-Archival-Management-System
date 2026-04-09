"""Exhibitions router — CRUD for exhibitions, pages, and content blocks.

Follows the Omeka S exhibit builder pattern: exhibitions contain pages,
pages contain blocks, blocks reference documents and other entities.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
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


class ExhibitionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=200)
    subtitle: str | None = None
    description: str | None = None
    credits: str | None = None
    cover_image_path: str | None = None
    header_image_path: str | None = None
    accent_color: str | None = None
    show_summary_page: bool = True
    is_published: bool = False


class ExhibitionUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    subtitle: str | None = None
    description: str | None = None
    credits: str | None = None
    cover_image_path: str | None = None
    header_image_path: str | None = None
    accent_color: str | None = None
    show_summary_page: bool | None = None
    is_published: bool | None = None


class ExhibitionOut(BaseModel):
    id: int
    title: str
    slug: str
    subtitle: str | None = None
    description: str | None = None
    is_published: bool = False
    sort_order: int = 0

    class Config:
        from_attributes = True


class PageCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=200)
    parent_page_id: int | None = None
    menu_title: str | None = None
    is_public: bool = True
    sort_order: int = 0


class PageUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    parent_page_id: int | None = None
    menu_title: str | None = None
    is_public: bool | None = None
    sort_order: int | None = None


class PageOut(BaseModel):
    id: int
    exhibition_id: int
    parent_page_id: int | None = None
    title: str
    slug: str
    menu_title: str | None = None
    is_public: bool = True
    sort_order: int = 0

    class Config:
        from_attributes = True


class BlockCreate(BaseModel):
    block_type: str = Field(
        description="html|file_with_text|gallery|document_metadata|map|"
        "timeline|table_of_contents|collection_browse|separator"
    )
    content: dict[str, Any]
    layout: str = "full"
    sort_order: int = 0


class BlockUpdate(BaseModel):
    block_type: str | None = None
    content: dict[str, Any] | None = None
    layout: str | None = None
    sort_order: int | None = None


class BlockOut(BaseModel):
    id: int
    page_id: int
    block_type: str
    content: dict[str, Any]
    layout: str = "full"
    sort_order: int = 0

    class Config:
        from_attributes = True


class BlockReorderRequest(BaseModel):
    block_ids: list[int] = Field(
        description="Ordered list of block IDs representing the desired sort order"
    )


# ---------------------------------------------------------------------------
# Exhibition CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[ExhibitionOut])
async def list_exhibitions(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all exhibitions with pagination."""
    from app.services import exhibition_service

    return await exhibition_service.list_exhibitions(db, page=page, per_page=per_page)


@router.post("", response_model=ExhibitionOut, status_code=status.HTTP_201_CREATED)
async def create_exhibition(
    body: ExhibitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Create a new exhibition."""
    from app.services import exhibition_service

    return await exhibition_service.create_exhibition(db, body, current_user)


@router.get("/{exhibition_id}", response_model=ExhibitionOut)
async def get_exhibition(
    exhibition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single exhibition by ID."""
    from app.services import exhibition_service

    exhibition = await exhibition_service.get_exhibition(db, exhibition_id)
    if exhibition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibition not found"
        )
    return exhibition


@router.patch("/{exhibition_id}", response_model=ExhibitionOut)
async def update_exhibition(
    exhibition_id: int,
    body: ExhibitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Update an exhibition's metadata."""
    from app.services import exhibition_service

    exhibition = await exhibition_service.update_exhibition(
        db, exhibition_id, body, current_user
    )
    if exhibition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibition not found"
        )
    return exhibition


@router.delete("/{exhibition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exhibition(
    exhibition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete an exhibition and all its pages and blocks."""
    from app.services import exhibition_service

    success = await exhibition_service.delete_exhibition(
        db, exhibition_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exhibition not found"
        )


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get("/{exhibition_id}/pages", response_model=list[PageOut])
async def list_pages(
    exhibition_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all pages for an exhibition (tree structure)."""
    from app.services import exhibition_service

    return await exhibition_service.list_pages(db, exhibition_id)


@router.post(
    "/{exhibition_id}/pages",
    response_model=PageOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_page(
    exhibition_id: int,
    body: PageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Create a new page within an exhibition."""
    from app.services import exhibition_service

    return await exhibition_service.create_page(
        db, exhibition_id, body, current_user
    )


@router.get("/{exhibition_id}/pages/{page_id}", response_model=PageOut)
async def get_page(
    exhibition_id: int,
    page_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single exhibition page with its blocks."""
    from app.services import exhibition_service

    page = await exhibition_service.get_page(db, exhibition_id, page_id)
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.patch("/{exhibition_id}/pages/{page_id}", response_model=PageOut)
async def update_page(
    exhibition_id: int,
    page_id: int,
    body: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Update an exhibition page."""
    from app.services import exhibition_service

    page = await exhibition_service.update_page(
        db, exhibition_id, page_id, body, current_user
    )
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


@router.delete(
    "/{exhibition_id}/pages/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_page(
    exhibition_id: int,
    page_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete an exhibition page and all its blocks."""
    from app.services import exhibition_service

    success = await exhibition_service.delete_page(
        db, exhibition_id, page_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


@router.post(
    "/{exhibition_id}/pages/{page_id}/blocks",
    response_model=BlockOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_block(
    exhibition_id: int,
    page_id: int,
    body: BlockCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Add a content block to an exhibition page."""
    from app.services import exhibition_service

    return await exhibition_service.create_block(
        db, exhibition_id, page_id, body, current_user
    )


@router.patch(
    "/{exhibition_id}/pages/{page_id}/blocks/{block_id}",
    response_model=BlockOut,
)
async def update_block(
    exhibition_id: int,
    page_id: int,
    block_id: int,
    body: BlockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Update a content block."""
    from app.services import exhibition_service

    block = await exhibition_service.update_block(
        db, exhibition_id, page_id, block_id, body, current_user
    )
    if block is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Block not found"
        )
    return block


@router.delete(
    "/{exhibition_id}/pages/{page_id}/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_block(
    exhibition_id: int,
    page_id: int,
    block_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Remove a content block from an exhibition page."""
    from app.services import exhibition_service

    success = await exhibition_service.delete_block(
        db, exhibition_id, page_id, block_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Block not found"
        )


@router.post(
    "/{exhibition_id}/pages/{page_id}/blocks/reorder",
    response_model=MessageResponse,
)
async def reorder_blocks(
    exhibition_id: int,
    page_id: int,
    body: BlockReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Set the sort order for all blocks on a page."""
    from app.services import exhibition_service

    await exhibition_service.reorder_blocks(
        db, exhibition_id, page_id, body.block_ids, current_user
    )
    return MessageResponse(detail="Blocks reordered")
