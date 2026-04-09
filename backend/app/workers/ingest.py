"""Watch folder ingest Celery tasks."""

import hashlib
import logging
import shutil
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.preservation_event import PreservationEvent
from app.models.watch_folder import WatchFolder
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(name="app.workers.ingest.poll_watch_folders")
def poll_watch_folders() -> dict:
    """Scan all active watch folders for new files."""
    with get_sync_session() as db:
        folders = db.execute(
            select(WatchFolder).where(WatchFolder.is_active.is_(True))
        ).scalars().all()

        total_ingested = 0
        for folder in folders:
            folder_path = Path(settings.STORAGE_ROOT) / folder.path
            if not folder_path.exists():
                logger.warning("Watch folder path does not exist: %s", folder_path)
                continue

            for file_path in folder_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith("."):
                    lock_file = file_path.with_suffix(file_path.suffix + ".processing")
                    if lock_file.exists():
                        continue

                    try:
                        lock_file.touch()
                        _ingest_file(db, file_path, folder)
                        total_ingested += 1
                    except Exception as e:
                        logger.error("Failed to ingest %s: %s", file_path, e)
                        db.add(PreservationEvent(
                            event_type="ingest",
                            event_outcome="failure",
                            event_detail=f"Watch folder ingest failed for {file_path.name}: {e}",
                            agent=f"watch_folder:{folder.id}",
                        ))
                        db.commit()
                    finally:
                        if lock_file.exists():
                            lock_file.unlink()

    return {"status": "complete", "ingested": total_ingested}


def _ingest_file(db: Session, file_path: Path, folder: WatchFolder) -> None:
    """Process a single file from a watch folder."""
    quarantine_dir = Path(settings.STORAGE_ROOT) / ".quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    quarantine_path = quarantine_dir / f"{uuid.uuid4()}_{file_path.name}"

    shutil.move(str(file_path), str(quarantine_path))

    # Compute hash
    h = hashlib.sha256()
    with open(quarantine_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    file_hash = h.hexdigest()

    # Detect MIME type
    import magic
    mime_type = magic.from_file(str(quarantine_path), mime=True)

    # Create document stub
    title = file_path.stem.replace("_", " ").replace("-", " ").title()
    doc = Document(
        title=title,
        description_status="draft",
        inbox_status="inbox",
        arrangement_node_id=folder.target_node_id,
    )
    db.add(doc)
    db.flush()

    # Move to permanent path
    permanent_dir = Path(settings.STORAGE_ROOT) / "files" / str(doc.id)
    permanent_dir.mkdir(parents=True, exist_ok=True)
    permanent_path = permanent_dir / file_path.name
    shutil.move(str(quarantine_path), str(permanent_path))

    stored_path = str(permanent_path.relative_to(Path(settings.STORAGE_ROOT)))

    # Create file record
    doc_file = DocumentFile(
        document_id=doc.id,
        filename=file_path.name,
        stored_path=stored_path,
        mime_type=mime_type,
        file_size_bytes=permanent_path.stat().st_size,
        file_hash_sha256=file_hash,
    )
    db.add(doc_file)

    # Log preservation event
    db.add(PreservationEvent(
        document_file_id=None,
        document_id=doc.id,
        event_type="ingest",
        event_outcome="success",
        event_detail=f"Ingested from watch folder: {folder.name}",
        agent=f"watch_folder:{folder.id}",
    ))

    db.commit()

    # Queue OCR if enabled
    if settings.OCR_ENABLED and mime_type in (
        "application/pdf", "image/jpeg", "image/png", "image/tiff", "image/webp"
    ):
        from app.workers.ocr import process_file
        process_file.delay(doc_file.id)

    logger.info("Ingested file %s as document %d", file_path.name, doc.id)
