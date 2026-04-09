"""Export-related Celery tasks (XMP embedding)."""

import logging
import shutil
import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(name="app.workers.export.embed_xmp_metadata")
def embed_xmp_metadata(document_id: int, file_id: int) -> dict:
    """Embed Dublin Core XMP metadata into a file for export."""
    with get_sync_session() as db:
        document = db.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

        file_record = db.execute(
            select(DocumentFile).where(DocumentFile.id == file_id)
        ).scalar_one_or_none()

        if not document or not file_record:
            return {"status": "error", "message": "Document or file not found"}

        source_path = Path(settings.STORAGE_ROOT) / file_record.stored_path
        export_dir = Path(settings.STORAGE_ROOT) / ".exports" / str(uuid.uuid4())
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / file_record.filename

        try:
            if file_record.mime_type == "application/pdf":
                from app.xmp.pdf import embed_dc_xmp
                from app.export.dublin_core import document_to_xmp_dict

                dc = document_to_xmp_dict(document)
                embed_dc_xmp(source_path, dc, output_path)
            else:
                shutil.copy2(str(source_path), str(output_path))

            return {
                "status": "success",
                "output_path": str(output_path),
            }

        except Exception as e:
            logger.error("XMP embedding failed: %s", e)
            if export_dir.exists():
                shutil.rmtree(str(export_dir))
            return {"status": "error", "message": str(e)}
