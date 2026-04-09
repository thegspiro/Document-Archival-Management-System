"""Review queue schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ReviewReason = Literal[
    "llm_suggestions", "manual_flag", "import", "initial_review", "integrity_failure"
]
ReviewPriority = Literal["low", "normal", "high"]


class ReviewQueueResponse(BaseModel):
    """Response for a review queue entry."""

    id: int
    document_id: int
    reason: ReviewReason
    assigned_to: int | None = None
    priority: ReviewPriority = "normal"
    notes: str | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewActionRequest(BaseModel):
    """Schema for POST /api/v1/review/{document_id}/approve or /reject.

    The ``field_decisions`` map lets a reviewer accept, edit, or reject each
    LLM/NER-suggested field independently (per CLAUDE.md §9.4).
    """

    notes: str | None = Field(default=None, description="Reviewer notes")
    field_decisions: dict[str, "FieldDecision"] | None = Field(
        default=None,
        description=(
            "Per-field decisions keyed by document field name. "
            "Only relevant when reviewing LLM or NER suggestions."
        ),
    )


class FieldDecision(BaseModel):
    """Decision for a single suggested field during review."""

    action: Literal["accept", "edit", "reject"]
    edited_value: Any | None = Field(
        default=None,
        description="New value when action is 'edit'. Ignored for accept/reject.",
    )


class ReviewAssignRequest(BaseModel):
    """Schema for PATCH /api/v1/review/{document_id}/assign."""

    assigned_to: int | None = Field(description="User ID to assign, or null to unassign")
    priority: ReviewPriority | None = None
    notes: str | None = None


# Rebuild for forward reference
ReviewActionRequest.model_rebuild()
