"""OCR Celery tasks."""

import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document_file import DocumentFile
from app.models.document_page import DocumentPage
from app.models.preservation_event import PreservationEvent
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    """Create a synchronous session for Celery tasks."""
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(
    name="app.workers.ocr.process_file",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_file(self, document_file_id: int) -> dict:
    """Run OCR on a document file using Tesseract."""
    with get_sync_session() as db:
        file_record = db.execute(
            select(DocumentFile).where(DocumentFile.id == document_file_id)
        ).scalar_one_or_none()

        if not file_record:
            logger.error("DocumentFile %d not found", document_file_id)
            return {"status": "error", "message": "File not found"}

        # Update status to processing
        db.execute(
            update(DocumentFile)
            .where(DocumentFile.id == document_file_id)
            .values(ocr_status="processing")
        )
        db.commit()

        try:
            import pytesseract
            from pathlib import Path

            file_path = Path(settings.STORAGE_ROOT) / file_record.stored_path
            full_text = ""

            if file_record.mime_type == "application/pdf":
                from pdf2image import convert_from_path

                images = convert_from_path(str(file_path))
                for page_num, image in enumerate(images, start=1):
                    page_text = pytesseract.image_to_string(
                        image, lang=settings.OCR_LANGUAGE
                    )
                    full_text += page_text + "\n"

                    # Update or create page record
                    page = db.execute(
                        select(DocumentPage).where(
                            DocumentPage.document_file_id == document_file_id,
                            DocumentPage.page_number == page_num,
                        )
                    ).scalar_one_or_none()

                    if page:
                        page.ocr_text = page_text
                    else:
                        db.add(DocumentPage(
                            document_file_id=document_file_id,
                            page_number=page_num,
                            ocr_text=page_text,
                        ))
            else:
                from PIL import Image

                image = Image.open(file_path)
                full_text = pytesseract.image_to_string(
                    image, lang=settings.OCR_LANGUAGE
                )

                page = db.execute(
                    select(DocumentPage).where(
                        DocumentPage.document_file_id == document_file_id,
                        DocumentPage.page_number == 1,
                    )
                ).scalar_one_or_none()

                if page:
                    page.ocr_text = full_text
                else:
                    db.add(DocumentPage(
                        document_file_id=document_file_id,
                        page_number=1,
                        ocr_text=full_text,
                    ))

            # Update file record
            db.execute(
                update(DocumentFile)
                .where(DocumentFile.id == document_file_id)
                .values(
                    ocr_status="complete",
                    ocr_text=full_text.strip(),
                    ocr_completed_at=datetime.now(tz=timezone.utc),
                )
            )

            # Log preservation event
            db.add(PreservationEvent(
                document_file_id=document_file_id,
                document_id=file_record.document_id,
                event_type="ocr",
                event_outcome="success",
                event_detail=f"OCR completed with Tesseract, language={settings.OCR_LANGUAGE}",
                agent="celery_worker",
            ))

            db.commit()
            logger.info("OCR completed for file %d", document_file_id)
            return {"status": "success", "file_id": document_file_id}

        except Exception as e:
            db.execute(
                update(DocumentFile)
                .where(DocumentFile.id == document_file_id)
                .values(
                    ocr_status="failed",
                    ocr_error=str(e),
                    ocr_attempt_count=DocumentFile.ocr_attempt_count + 1,
                )
            )
            db.add(PreservationEvent(
                document_file_id=document_file_id,
                document_id=file_record.document_id,
                event_type="ocr",
                event_outcome="failure",
                event_detail=f"OCR failed: {e}",
                agent="celery_worker",
            ))
            db.commit()
            raise
