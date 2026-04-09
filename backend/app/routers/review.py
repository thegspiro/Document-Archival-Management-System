"""Review queue router — manage documents pending review (LLM, NER, import, manual)."""

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


class ReviewItemOut(BaseModel):
    id: int
    document_id: int
    reason: str
    assigned_to: int | None = None
    priority: str = "normal"
    notes: str | None = None

    class Config:
        from_attributes = True


class ReviewApproveRequest(BaseModel):
    notes: str | None = None
    accepted_fields: dict[str, Any] | None = Field(
        default=None,
        description="Map of field name to accepted value for LLM/NER suggestions",
    )


class ReviewRejectRequest(BaseModel):
    notes: str | None = None


class ReviewAssignRequest(BaseModel):
    assigned_to: int | None = Field(
        description="User ID to assign to, or null to unassign"
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[ReviewItemOut])
async def list_review_queue(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    reason: str | None = Query(None, description="Filter by reason"),
    priority: str | None = Query(None, description="Filter by priority"),
    assigned_to: int | None = Query(None, description="Filter by assigned user"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """List items in the review queue with optional filters."""
    from app.services import review_service

    return await review_service.list_queue(
        db, page=page, per_page=per_page, reason=reason,
        priority=priority, assigned_to=assigned_to,
    )


@router.get("/{document_id}", response_model=ReviewItemOut)
async def get_review_item(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Retrieve the review queue entry for a specific document."""
    from app.services import review_service

    item = await review_service.get_review_item(db, document_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review item not found for this document",
        )
    return item


@router.post("/{document_id}/approve", response_model=MessageResponse)
async def approve_review(
    document_id: int,
    body: ReviewApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Approve a document in the review queue, optionally accepting LLM/NER suggestions."""
    from app.services import review_service

    await review_service.approve(db, document_id, body, current_user)
    return MessageResponse(detail="Review approved")


@router.post("/{document_id}/reject", response_model=MessageResponse)
async def reject_review(
    document_id: int,
    body: ReviewRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Reject a document's review, discarding suggestions."""
    from app.services import review_service

    await review_service.reject(db, document_id, body, current_user)
    return MessageResponse(detail="Review rejected")


@router.patch("/{document_id}/assign", response_model=ReviewItemOut)
async def assign_review(
    document_id: int,
    body: ReviewAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Assign or unassign a review queue item to a user."""
    from app.services import review_service

    item = await review_service.assign(db, document_id, body.assigned_to, current_user)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review item not found for this document",
        )
    return item
