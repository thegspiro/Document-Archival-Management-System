"""Common schemas used across the application — pagination, bulk actions, messages."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper matching the API convention in CLAUDE.md §14.1."""

    items: list[T]
    total: int = Field(description="Total number of records matching the query")
    page: int = Field(ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")

    model_config = ConfigDict(from_attributes=True)


class BulkActionRequest(BaseModel):
    """Request schema for bulk document operations (POST /api/v1/documents/bulk)."""

    document_ids: list[int] = Field(min_length=1, description="List of document IDs to act on")
    action: "BulkAction"


class BulkAction(BaseModel):
    """Describes the bulk action to perform and its parameters."""

    type: str = Field(
        description="Action type: apply_terms, remove_terms, assign_node, "
        "set_public, clear_inbox, add_to_review, export_zip, delete"
    )
    term_ids: list[int] | None = Field(
        default=None, description="Vocabulary term IDs for apply_terms / remove_terms"
    )
    node_id: int | None = Field(default=None, description="Arrangement node ID for assign_node")
    is_public: bool | None = Field(default=None, description="Public flag for set_public")
    reason: str | None = Field(
        default=None,
        description="Required reason text for delete action (logged to audit_log)",
    )


class MessageResponse(BaseModel):
    """Simple message response returned by actions that produce no resource body."""

    detail: str
    code: str | None = Field(default=None, description="Machine-readable status code")


class ErrorResponse(BaseModel):
    """Standard error envelope per §14.1."""

    detail: str
    code: str


class BulkActionResponse(BaseModel):
    """Summary returned after a bulk action completes."""

    affected: int = Field(description="Number of documents affected")
    detail: str = Field(description="Human-readable summary of what was done")


# Rebuild BulkActionRequest now that BulkAction is defined
BulkActionRequest.model_rebuild()
