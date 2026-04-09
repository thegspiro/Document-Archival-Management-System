"""Thumbnail generation Celery tasks."""

import logging
from pathlib import Path

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document_file import DocumentFile
from app.models.document_page import DocumentPage
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(name="app.workers.thumbnails.generate_thumbnails")
def generate_thumbnails(document_file_id: int) -> dict:
    """Generate thumbnails for a document file."""
    with get_sync_session() as db:
        file_record = db.execute(
            select(DocumentFile).where(DocumentFile.id == document_file_id)
        ).scalar_one_or_none()

        if not file_record:
            return {"status": "error", "message": "File not found"}

        file_path = Path(settings.STORAGE_ROOT) / file_record.stored_path
        thumb_dir = Path(settings.STORAGE_ROOT) / ".thumbnails" / str(document_file_id)
        thumb_dir.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image

            if file_record.mime_type == "application/pdf":
                from pdf2image import convert_from_path

                images = convert_from_path(str(file_path), first_page=1, last_page=50)
                for page_num, image in enumerate(images, start=1):
                    thumb_path = thumb_dir / f"{page_num}.webp"
                    image.thumbnail((300, 300))
                    image.save(str(thumb_path), "WEBP", quality=80)

                    # Update page thumbnail
                    relative_thumb = str(thumb_path.relative_to(Path(settings.STORAGE_ROOT)))
                    db.execute(
                        update(DocumentPage)
                        .where(
                            DocumentPage.document_file_id == document_file_id,
                            DocumentPage.page_number == page_num,
                        )
                        .values(thumbnail_path=relative_thumb)
                    )

                # Set file thumbnail to first page
                first_thumb = f".thumbnails/{document_file_id}/1.webp"
                db.execute(
                    update(DocumentFile)
                    .where(DocumentFile.id == document_file_id)
                    .values(thumbnail_path=first_thumb, page_count=len(images))
                )

            elif file_record.mime_type and file_record.mime_type.startswith("image/"):
                image = Image.open(file_path)
                thumb_path = thumb_dir / "1.webp"
                image.thumbnail((300, 300))
                image.save(str(thumb_path), "WEBP", quality=80)

                relative_thumb = str(thumb_path.relative_to(Path(settings.STORAGE_ROOT)))
                db.execute(
                    update(DocumentFile)
                    .where(DocumentFile.id == document_file_id)
                    .values(thumbnail_path=relative_thumb)
                )

            db.commit()
            logger.info("Thumbnails generated for file %d", document_file_id)
            return {"status": "success", "file_id": document_file_id}

        except Exception as e:
            logger.error("Thumbnail generation failed for file %d: %s", document_file_id, e)
            db.rollback()
            return {"status": "error", "message": str(e)}
