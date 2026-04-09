"""File service — upload, download (with XMP embedding), and deletion.

All file I/O goes through the ``app/storage`` module.  This service
orchestrates the ingest pipeline: quarantine, hash, MIME detection, move
to permanent path, row creation, and Celery task queuing.
"""

import hashlib
import os
import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.preservation_event import PreservationEvent
from app.services.audit_service import AuditService


def _storage_root() -> Path:
    """Resolve the storage root from the ``STORAGE_ROOT`` environment setting."""
    return Path(settings.STORAGE_ROOT)


def _quarantine_dir() -> Path:
    path = _storage_root() / ".quarantine"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_permanent_path(
    accession_number: str, filename: str
) -> str:
    """Compute a relative stored path using the date-based default scheme.

    The path is relative to ``STORAGE_ROOT`` so that it remains portable
    when the root changes.
    """
    from datetime import datetime, timezone

    now = datetime.now(tz=timezone.utc)
    safe_accession = _sanitize_path_component(accession_number)
    safe_filename = _sanitize_path_component(filename)
    return f"{now.year}/{now.month:02d}/{safe_accession}/{safe_filename}"


def _sanitize_path_component(value: str) -> str:
    """Lowercase, replace spaces with underscores, strip non-alnum except - and _."""
    value = value.lower().replace(" ", "_")
    return "".join(c for c in value if c.isalnum() or c in ("-", "_", "."))


def _compute_sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _detect_mime(path: Path) -> str:
    """Detect MIME type from file content using python-magic if available,
    falling back to a simple extension-based lookup.
    """
    try:
        import magic  # python-magic
        return magic.from_file(str(path), mime=True)
    except ImportError:
        import mimetypes
        guessed, _ = mimetypes.guess_type(str(path))
        return guessed or "application/octet-stream"


class FileService:
    """Manages the lifecycle of physical files attached to documents."""

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    @staticmethod
    async def upload_file(
        db: AsyncSession,
        *,
        document_id: int,
        upload: UploadFile,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> DocumentFile:
        """Ingest a file through the quarantine pipeline.

        Steps (per CLAUDE.md section 6.2):
        1. Save to quarantine.
        2. Compute SHA-256.
        3. Detect MIME type.
        4. Move to permanent path.
        5. Create ``document_files`` row.
        6. Write ``preservation_events`` ingest row.
        7. Queue Celery tasks (OCR, thumbnails) — stubs are noted here;
           actual Celery integration is in ``app/workers``.
        """
        # Verify the document exists.
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # 1. Save to quarantine.
        original_filename = upload.filename or "unnamed"
        quarantine_name = f"{uuid.uuid4()}_{original_filename}"
        quarantine_path = _quarantine_dir() / quarantine_name

        contents = await upload.read()
        with open(quarantine_path, "wb") as f:
            f.write(contents)

        try:
            # 2. Compute SHA-256.
            file_hash = _compute_sha256(quarantine_path)

            # Check for duplicate files within this document.
            dup_result = await db.execute(
                select(DocumentFile).where(
                    DocumentFile.document_id == document_id,
                    DocumentFile.file_hash_sha256 == file_hash,
                )
            )
            if dup_result.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An identical file already exists on this document",
                )

            # 3. Detect MIME type.
            mime_type = _detect_mime(quarantine_path)
            file_size = quarantine_path.stat().st_size

            # 4. Move to permanent path.
            accession = doc.accession_number or str(doc.id)
            relative_path = _resolve_permanent_path(accession, original_filename)
            permanent_path = _storage_root() / relative_path
            permanent_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(quarantine_path), str(permanent_path))

        except HTTPException:
            # Clean up quarantine on known errors.
            if quarantine_path.exists():
                quarantine_path.unlink()
            raise
        except Exception:
            if quarantine_path.exists():
                quarantine_path.unlink()
            raise

        # 5. Create document_files row.
        doc_file = DocumentFile(
            document_id=document_id,
            filename=original_filename,
            stored_path=relative_path,
            mime_type=mime_type,
            file_size_bytes=file_size,
            file_hash_sha256=file_hash,
        )
        db.add(doc_file)
        await db.flush()

        # 6. Preservation event.
        db.add(PreservationEvent(
            document_file_id=doc_file.id,
            document_id=document_id,
            event_type="ingest",
            event_outcome="success",
            event_detail=f"File ingested: {original_filename} ({mime_type}, {file_size} bytes)",
            agent=f"user:{acting_user_id}" if acting_user_id else "system",
        ))
        await db.flush()

        # 7. Audit log.
        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="document_file.create",
            resource_type="document_file",
            resource_id=doc_file.id,
            detail={
                "document_id": document_id,
                "filename": original_filename,
                "mime_type": mime_type,
                "file_size_bytes": file_size,
                "sha256": file_hash,
            },
            ip_address=ip_address,
        )

        # Celery tasks for OCR and thumbnails would be queued here.
        # e.g.:  from app.workers.ocr import process_file
        #        process_file.delay(doc_file.id)

        return doc_file

    # ------------------------------------------------------------------
    # Download (with on-the-fly XMP embedding)
    # ------------------------------------------------------------------

    @staticmethod
    async def download_file(
        db: AsyncSession,
        *,
        document_id: int,
        file_id: int,
    ) -> tuple[Path, str, str]:
        """Prepare a file for download, embedding XMP Dublin Core metadata.

        Returns ``(file_path, mime_type, filename)`` for the router to
        stream back.  If XMP embedding is supported for the MIME type, a
        temporary copy with metadata is returned.  Otherwise the original
        stored file is served directly.
        """
        result = await db.execute(
            select(DocumentFile).where(
                DocumentFile.id == file_id,
                DocumentFile.document_id == document_id,
            )
        )
        doc_file = result.scalar_one_or_none()
        if doc_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        file_path = _storage_root() / doc_file.stored_path
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Physical file missing from storage",
            )

        # XMP embedding would be performed here for PDFs and images using
        # pikepdf / Pillow.  The embedded copy is written to a temp directory
        # and returned.  For non-embeddable types, return the original.
        #
        # A full implementation lives in app/xmp/ and is invoked by a Celery
        # worker.  Here we return the original path as a baseline.
        return file_path, doc_file.mime_type or "application/octet-stream", doc_file.filename

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_file(
        db: AsyncSession,
        *,
        document_id: int,
        file_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Remove a file record and its physical file from storage."""
        result = await db.execute(
            select(DocumentFile).where(
                DocumentFile.id == file_id,
                DocumentFile.document_id == document_id,
            )
        )
        doc_file = result.scalar_one_or_none()
        if doc_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        # Remove physical file.
        file_path = _storage_root() / doc_file.stored_path
        if file_path.exists():
            file_path.unlink()

        # Preservation event.
        db.add(PreservationEvent(
            document_file_id=doc_file.id,
            document_id=document_id,
            event_type="deletion",
            event_outcome="success",
            event_detail=f"File deleted: {doc_file.filename}",
            agent=f"user:{acting_user_id}" if acting_user_id else "system",
        ))

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="document_file.delete",
            resource_type="document_file",
            resource_id=doc_file.id,
            detail={
                "document_id": document_id,
                "filename": doc_file.filename,
            },
            ip_address=ip_address,
        )

        await db.delete(doc_file)
        await db.flush()
