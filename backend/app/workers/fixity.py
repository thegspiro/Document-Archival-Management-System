"""Fixity check Celery tasks (OAIS requirement)."""

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document_file import DocumentFile
from app.models.fixity_check import FixityCheck
from app.models.preservation_event import PreservationEvent
from app.models.review_queue import ReviewQueue
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@celery_app.task(name="app.workers.fixity.check_file")
def check_file(document_file_id: int) -> dict:
    """Run a fixity check on a single document file."""
    with get_sync_session() as db:
        file_record = db.execute(
            select(DocumentFile).where(DocumentFile.id == document_file_id)
        ).scalar_one_or_none()

        if not file_record:
            return {"status": "error", "message": "File not found"}

        stored_hash = file_record.file_hash_sha256 or ""
        file_path = Path(settings.STORAGE_ROOT) / file_record.stored_path

        if not file_path.exists():
            outcome = "file_missing"
            computed_hash = ""
        else:
            computed_hash = compute_sha256(file_path)
            outcome = "match" if computed_hash == stored_hash else "mismatch"

        # Record fixity check
        db.add(FixityCheck(
            document_file_id=document_file_id,
            stored_hash=stored_hash,
            computed_hash=computed_hash,
            outcome=outcome,
            checked_by="celery_beat",
        ))

        # Log preservation event
        event_outcome = "success" if outcome == "match" else "failure"
        db.add(PreservationEvent(
            document_file_id=document_file_id,
            document_id=file_record.document_id,
            event_type="fixity_check",
            event_outcome=event_outcome,
            event_detail=f"Fixity check: {outcome}. Stored: {stored_hash[:16]}..., Computed: {computed_hash[:16]}...",
            agent="celery_beat",
        ))

        # Handle failures
        if outcome in ("mismatch", "file_missing"):
            existing = db.execute(
                select(ReviewQueue).where(
                    ReviewQueue.document_id == file_record.document_id
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(ReviewQueue(
                    document_id=file_record.document_id,
                    reason="integrity_failure",
                    priority="high",
                    notes=f"Fixity check failed: {outcome}",
                ))
            logger.warning(
                "Fixity check FAILED for file %d: %s", document_file_id, outcome
            )

        db.commit()
        return {"status": outcome, "file_id": document_file_id}


@celery_app.task(name="app.workers.fixity.run_scheduled_fixity")
def run_scheduled_fixity() -> dict:
    """Run fixity checks on all files. Scheduled via Celery beat."""
    with get_sync_session() as db:
        files = db.execute(
            select(DocumentFile.id).where(DocumentFile.file_hash_sha256.isnot(None))
        ).scalars().all()

    checked = 0
    for file_id in files:
        check_file.delay(file_id)
        checked += 1

    logger.info("Queued fixity checks for %d files", checked)
    return {"status": "queued", "count": checked}
