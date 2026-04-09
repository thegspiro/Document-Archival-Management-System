"""Document router — full CRUD, file management, relationships, annotations,
versioning, citation, export, deaccession, availability, and bulk operations.

This is the largest router in ADMS because documents are the core domain entity.
All business logic is delegated to service modules.
"""

from datetime import date
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.common import (
    BulkActionRequest,
    BulkActionResponse,
    MessageResponse,
    PaginatedResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    arrangement_node_id: int | None = None
    date_display: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    level_of_description: str = "item"
    extent: str | None = None
    creator_id: int | None = None
    scope_and_content: str | None = None
    language_of_material: str | None = None
    document_type_id: int | None = None
    is_public: bool = False


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=1000)
    arrangement_node_id: int | None = None
    date_display: str | None = None
    date_start: date | None = None
    date_end: date | None = None
    level_of_description: str | None = None
    extent: str | None = None
    creator_id: int | None = None
    scope_and_content: str | None = None
    access_conditions: str | None = None
    reproduction_conditions: str | None = None
    language_of_material: str | None = None
    physical_characteristics: str | None = None
    finding_aids: str | None = None
    location_of_originals: str | None = None
    location_of_copies: str | None = None
    related_units: str | None = None
    publication_note: str | None = None
    general_note: str | None = None
    archivists_note: str | None = None
    administrative_history: str | None = None
    archival_history: str | None = None
    immediate_source: str | None = None
    appraisal_notes: str | None = None
    accruals: str | None = None
    system_of_arrangement: str | None = None
    rules_or_conventions: str | None = None
    description_status: str | None = None
    copyright_status: str | None = None
    rights_holder: str | None = None
    rights_basis: str | None = None
    rights_note: str | None = None
    embargo_end_date: date | None = None
    document_type_id: int | None = None
    physical_format_id: int | None = None
    condition_id: int | None = None
    original_location: str | None = None
    scan_date: date | None = None
    is_public: bool | None = None
    public_title: str | None = None
    has_content_advisory: bool | None = None
    content_advisory_note: str | None = None
    geo_latitude: float | None = None
    geo_longitude: float | None = None
    geo_location_name: str | None = None
    version_label: str | None = None


class DocumentOut(BaseModel):
    id: int
    accession_number: str | None = None
    title: str
    date_display: str | None = None
    description_completeness: str = "none"
    is_public: bool = False
    inbox_status: str = "inbox"
    review_status: str = "none"

    class Config:
        from_attributes = True


class DocumentFileOut(BaseModel):
    id: int
    document_id: int
    filename: str
    mime_type: str | None = None
    file_size_bytes: int | None = None
    ocr_status: str = "none"
    thumbnail_path: str | None = None

    class Config:
        from_attributes = True


class PageUpdate(BaseModel):
    ocr_text: str | None = None
    notes: str | None = None
    is_public: bool | None = None


class PageOut(BaseModel):
    id: int
    document_file_id: int
    page_number: int
    ocr_text: str | None = None
    notes: str | None = None
    is_public: bool = False

    class Config:
        from_attributes = True


class RelationshipCreate(BaseModel):
    target_document_id: int
    relationship_type_id: int
    description: str | None = None


class RelationshipOut(BaseModel):
    id: int
    source_document_id: int
    target_document_id: int
    relationship_type_id: int
    description: str | None = None

    class Config:
        from_attributes = True


class AuthorityLinkCreate(BaseModel):
    authority_id: int
    role_id: int
    notes: str | None = None


class AuthorityLinkUpdate(BaseModel):
    role_id: int | None = None
    notes: str | None = None


class AuthorityLinkOut(BaseModel):
    id: int
    document_id: int
    authority_id: int
    role_id: int
    notes: str | None = None

    class Config:
        from_attributes = True


class LocationLinkCreate(BaseModel):
    location_id: int
    link_type: str = "mentioned"
    notes: str | None = None


class LocationLinkOut(BaseModel):
    id: int
    document_id: int
    location_id: int
    link_type: str
    notes: str | None = None

    class Config:
        from_attributes = True


class AnnotationCreate(BaseModel):
    document_file_id: int
    document_page_id: int | None = None
    annotation_type: str = Field(description="region | text_range")
    region_geometry: dict[str, float] | None = None
    text_range: dict[str, Any] | None = None
    body: str = Field(min_length=1)


class AnnotationUpdate(BaseModel):
    body: str | None = None
    region_geometry: dict[str, float] | None = None
    text_range: dict[str, Any] | None = None


class AnnotationOut(BaseModel):
    id: int
    document_id: int
    annotation_type: str
    body: str
    is_resolved: bool = False
    created_by: int | None = None

    class Config:
        from_attributes = True


class VersionGroupCreate(BaseModel):
    """Confirm creation of a version group from this document."""

    pass


class NewVersionCreate(BaseModel):
    """Metadata for the new version (inherits from canonical by default)."""

    title: str | None = None
    version_label: str | None = None


class JoinGroupRequest(BaseModel):
    target_group_id: int | None = None
    target_document_id: int | None = None
    version_number: int | None = None


class MakeUnavailableRequest(BaseModel):
    reason: str
    unavailable_until: date | None = None
    tombstone_disclosure: str = "accession_only"


class DeaccessionProposeRequest(BaseModel):
    reason_code_id: int | None = None
    reason_note: str = Field(min_length=1)
    disposition: str = Field(description="destroyed|transferred|returned|sold|donated")
    transfer_destination: str | None = None


class PreservationEventOut(BaseModel):
    id: int
    event_type: str
    event_outcome: str
    event_detail: str | None = None
    agent: str | None = None
    event_datetime: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[DocumentOut])
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    accession: str | None = Query(None, description="Exact accession number lookup"),
    inbox_status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List documents with pagination and optional filters."""
    from app.services import document_service

    return await document_service.list_documents(
        db, page=page, per_page=per_page, accession=accession,
        inbox_status=inbox_status, user=current_user,
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def create_document(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor", "intern",
    )),
) -> Any:
    """Create a new document record."""
    from app.services import document_service

    return await document_service.create_document(db, body, current_user)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve a single document by ID."""
    from app.services import document_service

    doc = await document_service.get_document(db, document_id, current_user)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.patch("/{document_id}", response_model=DocumentOut)
async def update_document(
    document_id: int,
    body: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update document metadata fields."""
    from app.services import document_service

    doc = await document_service.update_document(db, document_id, body, current_user)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> None:
    """Delete a document. Prefer the deaccession workflow for permanent removal."""
    from app.services import document_service

    success = await document_service.delete_document(db, document_id, current_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------


@router.post(
    "/{document_id}/files",
    response_model=DocumentFileOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    document_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor", "intern",
    )),
) -> Any:
    """Upload a file to a document. Triggers ingest pipeline (hash, Siegfried, OCR)."""
    from app.services import document_service

    return await document_service.upload_file(db, document_id, file, current_user)


@router.get("/{document_id}/files/{file_id}/download")
async def download_file(
    document_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download a document file with XMP Dublin Core metadata embedded."""
    from app.services import document_service

    content, media_type, filename = await document_service.download_file(
        db, document_id, file_id, current_user
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{document_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    document_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin", "archivist")),
) -> None:
    """Remove a file from a document."""
    from app.services import document_service

    success = await document_service.delete_file(db, document_id, file_id, current_user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.post(
    "/{document_id}/files/{file_id}/retry-ocr",
    response_model=MessageResponse,
)
async def retry_ocr(
    document_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> MessageResponse:
    """Re-queue OCR for a file that previously failed. Resets attempt counter."""
    from app.services import document_service

    await document_service.retry_ocr(db, document_id, file_id, current_user)
    return MessageResponse(detail="OCR re-queued")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@router.get("/{document_id}/pages", response_model=list[PageOut])
async def list_pages(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all pages for a document's files."""
    from app.services import document_service

    return await document_service.list_pages(db, document_id, current_user)


@router.patch("/{document_id}/pages/{page_id}", response_model=PageOut)
async def update_page(
    document_id: int,
    page_id: int,
    body: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update a document page (OCR text, notes, public flag)."""
    from app.services import document_service

    page = await document_service.update_page(
        db, document_id, page_id, body, current_user
    )
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


@router.get("/{document_id}/relationships", response_model=list[RelationshipOut])
async def list_relationships(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all relationships for a document (both directions)."""
    from app.services import document_service

    return await document_service.list_relationships(db, document_id, current_user)


@router.post(
    "/{document_id}/relationships",
    response_model=RelationshipOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_relationship(
    document_id: int,
    body: RelationshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a directional relationship between two documents."""
    from app.services import document_service

    return await document_service.create_relationship(
        db, document_id, body, current_user
    )


@router.delete(
    "/{document_id}/relationships/{rel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_relationship(
    document_id: int,
    rel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove a document relationship."""
    from app.services import document_service

    success = await document_service.delete_relationship(
        db, document_id, rel_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found"
        )


# ---------------------------------------------------------------------------
# Authority links
# ---------------------------------------------------------------------------


@router.get("/{document_id}/authority-links", response_model=list[AuthorityLinkOut])
async def list_authority_links(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all authority record links for a document (non-creator roles)."""
    from app.services import document_service

    return await document_service.list_authority_links(db, document_id, current_user)


@router.post(
    "/{document_id}/authority-links",
    response_model=AuthorityLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_authority_link(
    document_id: int,
    body: AuthorityLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Link an authority record to a document with a specific role."""
    from app.services import document_service

    return await document_service.create_authority_link(
        db, document_id, body, current_user
    )


@router.patch(
    "/{document_id}/authority-links/{link_id}",
    response_model=AuthorityLinkOut,
)
async def update_authority_link(
    document_id: int,
    link_id: int,
    body: AuthorityLinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update an authority-document link (change role or notes)."""
    from app.services import document_service

    link = await document_service.update_authority_link(
        db, document_id, link_id, body, current_user
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority link not found"
        )
    return link


@router.delete(
    "/{document_id}/authority-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_authority_link(
    document_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove an authority record link from a document."""
    from app.services import document_service

    success = await document_service.delete_authority_link(
        db, document_id, link_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Authority link not found"
        )


# ---------------------------------------------------------------------------
# Location links
# ---------------------------------------------------------------------------


@router.get("/{document_id}/location-links", response_model=list[LocationLinkOut])
async def list_location_links(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all locations linked to a document."""
    from app.services import document_service

    return await document_service.list_location_links(db, document_id, current_user)


@router.post(
    "/{document_id}/location-links",
    response_model=LocationLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_location_link(
    document_id: int,
    body: LocationLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Link a location to a document."""
    from app.services import document_service

    return await document_service.create_location_link(
        db, document_id, body, current_user
    )


@router.delete(
    "/{document_id}/location-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_location_link(
    document_id: int,
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Remove a location link from a document."""
    from app.services import document_service

    success = await document_service.delete_location_link(
        db, document_id, link_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location link not found"
        )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.get("/{document_id}/events", response_model=list[Any])
async def list_document_events(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List events linked to this document."""
    from app.services import document_service

    return await document_service.list_document_events(db, document_id, current_user)


# ---------------------------------------------------------------------------
# Annotations
# ---------------------------------------------------------------------------


@router.get("/{document_id}/annotations", response_model=list[AnnotationOut])
async def list_annotations(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor", "intern",
    )),
) -> Any:
    """List all annotations on a document. Staff only (viewers get 403)."""
    from app.services import annotation_service

    return await annotation_service.list_annotations(db, document_id, current_user)


@router.post(
    "/{document_id}/annotations",
    response_model=AnnotationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_annotation(
    document_id: int,
    body: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Create a region or text-range annotation on a document page."""
    from app.services import annotation_service

    return await annotation_service.create_annotation(
        db, document_id, body, current_user
    )


@router.patch(
    "/{document_id}/annotations/{ann_id}",
    response_model=AnnotationOut,
)
async def update_annotation(
    document_id: int,
    ann_id: int,
    body: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Update an annotation's body or geometry."""
    from app.services import annotation_service

    ann = await annotation_service.update_annotation(
        db, document_id, ann_id, body, current_user
    )
    if ann is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found"
        )
    return ann


@router.delete(
    "/{document_id}/annotations/{ann_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_annotation(
    document_id: int,
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> None:
    """Delete an annotation."""
    from app.services import annotation_service

    success = await annotation_service.delete_annotation(
        db, document_id, ann_id, current_user
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found"
        )


@router.post(
    "/{document_id}/annotations/{ann_id}/resolve",
    response_model=AnnotationOut,
)
async def resolve_annotation(
    document_id: int,
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Mark an annotation as resolved."""
    from app.services import annotation_service

    ann = await annotation_service.resolve_annotation(
        db, document_id, ann_id, current_user
    )
    if ann is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found"
        )
    return ann


@router.post(
    "/{document_id}/annotations/{ann_id}/reopen",
    response_model=AnnotationOut,
)
async def reopen_annotation(
    document_id: int,
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist", "contributor",
    )),
) -> Any:
    """Re-open a previously resolved annotation."""
    from app.services import annotation_service

    ann = await annotation_service.reopen_annotation(
        db, document_id, ann_id, current_user
    )
    if ann is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found"
        )
    return ann


# ---------------------------------------------------------------------------
# NER
# ---------------------------------------------------------------------------


@router.post("/{document_id}/run-ner", response_model=MessageResponse)
async def run_ner(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Trigger the NER pipeline on a document's OCR text."""
    from app.services import ner_service

    await ner_service.trigger_ner(db, document_id, current_user)
    return MessageResponse(detail="NER processing queued")


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------


@router.get("/{document_id}/versions", response_model=list[DocumentOut])
async def list_versions(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all versions in the document's version group."""
    from app.services import version_service

    return await version_service.list_versions(db, document_id, current_user)


@router.post(
    "/{document_id}/version-group",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version_group(
    document_id: int,
    body: VersionGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Create a version group from an unversioned document (Case A)."""
    from app.services import version_service

    await version_service.create_version_group(db, document_id, current_user)
    return MessageResponse(detail="Version group created")


@router.post(
    "/{document_id}/new-version",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_new_version(
    document_id: int,
    body: NewVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Add a new version to an existing version group (Case B)."""
    from app.services import version_service

    return await version_service.add_new_version(db, document_id, body, current_user)


@router.post(
    "/{document_id}/join-group",
    response_model=MessageResponse,
)
async def join_group(
    document_id: int,
    body: JoinGroupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Add this document to an existing version group (Case C)."""
    from app.services import version_service

    await version_service.join_group(db, document_id, body, current_user)
    return MessageResponse(detail="Document added to version group")


@router.post(
    "/{document_id}/set-canonical",
    response_model=MessageResponse,
)
async def set_canonical(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Promote this version to canonical within its version group."""
    from app.services import version_service

    await version_service.set_canonical(db, document_id, current_user)
    return MessageResponse(detail="Version set as canonical")


@router.post(
    "/{document_id}/set-public-version",
    response_model=MessageResponse,
)
async def set_public_version(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Promote this version to the public-facing version."""
    from app.services import version_service

    await version_service.set_public_version(db, document_id, current_user)
    return MessageResponse(detail="Public version set")


# ---------------------------------------------------------------------------
# Citation and export
# ---------------------------------------------------------------------------


@router.get("/{document_id}/cite")
async def cite_document(
    document_id: int,
    format: str = Query("chicago_note", description="Citation format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate a citation for a document in the requested format."""
    from app.services import citation_service

    result = await citation_service.cite_document(db, document_id, format)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return result


@router.post(
    "/{document_id}/cite/zotero-push",
    response_model=MessageResponse,
)
async def zotero_push(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Push document citation to the user's configured Zotero library."""
    from app.services import citation_service

    await citation_service.zotero_push(db, document_id, current_user)
    return MessageResponse(detail="Pushed to Zotero")


@router.get("/{document_id}/export")
async def export_document(
    document_id: int,
    format: str = Query(..., description="dc_xml | dc_json | mets"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Export document metadata in the specified format."""
    from app.services import export_service

    content, media_type, filename = await export_service.export_document(
        db, document_id, format, current_user
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Preservation events
# ---------------------------------------------------------------------------


@router.get(
    "/{document_id}/preservation-events",
    response_model=list[PreservationEventOut],
)
async def list_preservation_events(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all preservation events for a document."""
    from app.services import preservation_service

    return await preservation_service.list_document_events(
        db, document_id, current_user
    )


# ---------------------------------------------------------------------------
# Availability and tombstone
# ---------------------------------------------------------------------------


@router.post(
    "/{document_id}/make-unavailable",
    response_model=MessageResponse,
)
async def make_unavailable(
    document_id: int,
    body: MakeUnavailableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Set a document to temporarily unavailable with a tombstone."""
    from app.services import document_service

    await document_service.make_unavailable(db, document_id, body, current_user)
    return MessageResponse(detail="Document marked as temporarily unavailable")


@router.post(
    "/{document_id}/restore",
    response_model=MessageResponse,
)
async def restore_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Restore a temporarily unavailable document to available status."""
    from app.services import document_service

    await document_service.restore_document(db, document_id, current_user)
    return MessageResponse(detail="Document restored")


# ---------------------------------------------------------------------------
# Deaccession workflow
# ---------------------------------------------------------------------------


@router.post(
    "/{document_id}/deaccession/propose",
    response_model=MessageResponse,
)
async def deaccession_propose(
    document_id: int,
    body: DeaccessionProposeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Propose a document for deaccession."""
    from app.services import deaccession_service

    await deaccession_service.propose(db, document_id, body, current_user)
    return MessageResponse(detail="Deaccession proposed")


@router.post(
    "/{document_id}/deaccession/approve",
    response_model=MessageResponse,
)
async def deaccession_approve(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> MessageResponse:
    """Approve a deaccession proposal. Admin only."""
    from app.services import deaccession_service

    await deaccession_service.approve(db, document_id, current_user)
    return MessageResponse(detail="Deaccession approved")


@router.post(
    "/{document_id}/deaccession/execute",
    response_model=MessageResponse,
)
async def deaccession_execute(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "admin")),
) -> MessageResponse:
    """Execute an approved deaccession — writes log and removes physical file."""
    from app.services import deaccession_service

    await deaccession_service.execute(db, document_id, current_user)
    return MessageResponse(detail="Deaccession complete")


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_action(
    body: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Execute a bulk action on multiple documents."""
    from app.services import bulk_service

    return await bulk_service.execute_bulk(db, body, current_user)
