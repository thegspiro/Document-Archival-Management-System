"""Document file and page response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OcrStatus = Literal["none", "queued", "processing", "complete", "failed"]
ImageQualityRating = Literal[
    "preservation_master", "production_master", "access_copy", "unknown"
]


class DocumentPageResponse(BaseModel):
    """Response for a single page within a document file."""

    id: int
    document_file_id: int
    page_number: int
    ocr_text: str | None = None
    notes: str | None = None
    is_public: bool = False
    thumbnail_path: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentFileResponse(BaseModel):
    """Full response for a document file including technical and preservation metadata."""

    id: int
    document_id: int
    filename: str
    stored_path: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    file_hash_sha256: str | None = None
    page_count: int = 1
    sort_order: int = 0

    # OCR
    ocr_status: OcrStatus = "none"
    ocr_text: str | None = None
    ocr_completed_at: datetime | None = None
    ocr_error: str | None = None
    ocr_attempt_count: int = 0
    thumbnail_path: str | None = None

    # Technical metadata (NARA/FADGI)
    scan_resolution_ppi: int | None = None
    bit_depth: int | None = None
    color_space: str | None = None
    scanner_make: str | None = None
    scanner_model: str | None = None
    scanning_software: str | None = None
    image_quality_rating: ImageQualityRating = "unknown"

    # Format characterization (PREMIS / OAIS)
    format_name: str | None = None
    format_version: str | None = None
    format_puid: str | None = None
    format_registry: str = "PRONOM"
    format_validated: bool = False
    format_validated_at: datetime | None = None
    preservation_warning: str | None = None

    # Nested pages
    pages: list[DocumentPageResponse] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentPageUpdate(BaseModel):
    """Schema for PATCH /api/v1/documents/{id}/pages/{page_id}."""

    notes: str | None = None
    is_public: bool | None = None
