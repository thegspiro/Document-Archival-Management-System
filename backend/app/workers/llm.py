"""LLM metadata suggestion Celery tasks."""

import logging

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.review_queue import ReviewQueue
from app.models.system_setting import SystemSetting
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(name="app.workers.llm.suggest_metadata", bind=True)
def suggest_metadata(self, document_id: int) -> dict:
    """Generate LLM metadata suggestions for a document."""
    if settings.LLM_PROVIDER == "none" or not settings.LLM_PROVIDER:
        return {"status": "skipped", "reason": "LLM disabled"}

    with get_sync_session() as db:
        document = db.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

        if not document:
            return {"status": "error", "message": "Document not found"}

        # Get OCR text from files
        files = db.execute(
            select(DocumentFile).where(
                DocumentFile.document_id == document_id,
                DocumentFile.ocr_status == "complete",
            )
        ).scalars().all()

        ocr_text = "\n".join(f.ocr_text for f in files if f.ocr_text)
        if not ocr_text:
            return {"status": "skipped", "reason": "No OCR text available"}

        # Get LLM settings
        require_review_setting = db.execute(
            select(SystemSetting).where(SystemSetting.key == "llm.require_review")
        ).scalar_one_or_none()
        require_review = True
        if require_review_setting and require_review_setting.value is not None:
            require_review = require_review_setting.value.get("value", True)

        enabled_fields_setting = db.execute(
            select(SystemSetting).where(
                SystemSetting.key == "llm.enabled_suggestion_fields"
            )
        ).scalar_one_or_none()
        enabled_fields = []
        if enabled_fields_setting and enabled_fields_setting.value:
            enabled_fields = enabled_fields_setting.value.get("value", [])

        if not enabled_fields:
            return {"status": "skipped", "reason": "No suggestion fields enabled"}

        try:
            from app.llm.factory import get_llm_adapter

            adapter = get_llm_adapter()
            suggestions = adapter.suggest_metadata_sync(
                ocr_text=ocr_text,
                enabled_fields=enabled_fields,
            )

            # Store suggestions
            db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(llm_suggestions=suggestions)
            )

            if require_review:
                db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(review_status="pending")
                )
                existing = db.execute(
                    select(ReviewQueue).where(ReviewQueue.document_id == document_id)
                ).scalar_one_or_none()
                if not existing:
                    db.add(ReviewQueue(
                        document_id=document_id,
                        reason="llm_suggestions",
                        priority="normal",
                    ))

            db.commit()
            logger.info("LLM suggestions generated for document %d", document_id)
            return {"status": "success", "document_id": document_id}

        except Exception as e:
            logger.error("LLM suggestion failed for document %d: %s", document_id, e)
            db.rollback()
            return {"status": "error", "message": str(e)}
