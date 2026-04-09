"""CSV import router — upload, validate, review, confirm, and discard import jobs."""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ImportJobOut:
    """Inline schema — mirrors csv_imports table."""

    id: int
    filename: str
    import_mode: str
    status: str
    total_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int
    imported_rows: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/template")
async def download_template(
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Response:
    """Download the official ADMS CSV import template."""
    from app.services import import_service

    content, filename = await import_service.get_template()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("", response_model=PaginatedResponse[Any])
async def list_imports(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """List all import jobs for the current user."""
    from app.services import import_service

    return await import_service.list_imports(
        db, page=page, per_page=per_page, user=current_user,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    file: UploadFile = File(...),
    import_mode: str = Query("template", description="template | mapped"),
    target_node_id: int | None = Query(None, description="Default collection for imports"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Upload a CSV file and begin the validation pipeline."""
    from app.services import import_service

    return await import_service.create_import(
        db, file, import_mode=import_mode,
        target_node_id=target_node_id, user=current_user,
    )


@router.get("/{import_id}")
async def get_import(
    import_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> Any:
    """Retrieve an import job's status and validation report."""
    from app.services import import_service

    job = await import_service.get_import(db, import_id, current_user)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
    return job


@router.post("/{import_id}/confirm", response_model=MessageResponse)
async def confirm_import(
    import_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> MessageResponse:
    """Execute a validated import after user review and confirmation."""
    from app.services import import_service

    await import_service.confirm_import(db, import_id, current_user)
    return MessageResponse(detail="Import execution started")


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def discard_import(
    import_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(
        "superadmin", "admin", "archivist",
    )),
) -> None:
    """Discard an import job and its uploaded file."""
    from app.services import import_service

    success = await import_service.discard_import(db, import_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
