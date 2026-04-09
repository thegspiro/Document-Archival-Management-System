"""Description completeness recomputation tasks."""

import logging
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.institution_description_standard import InstitutionDescriptionStandard
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


@celery_app.task(name="app.workers.description.recompute_completeness")
def recompute_completeness(document_id: int) -> dict:
    """Recompute description completeness for a single document."""
    with get_sync_session() as db:
        document = db.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

        if not document:
            return {"status": "error", "message": "Document not found"}

        standards = db.execute(
            select(InstitutionDescriptionStandard).order_by(
                InstitutionDescriptionStandard.level
            )
        ).scalars().all()

        level_order = ["minimal", "standard", "full"]
        achieved_level = "none"

        for standard in sorted(standards, key=lambda s: level_order.index(s.level)):
            required_fields = standard.required_fields
            if not isinstance(required_fields, list):
                continue

            all_satisfied = True
            for field_name in required_fields:
                value = getattr(document, field_name, None)
                if value is None or (isinstance(value, str) and not value.strip()):
                    all_satisfied = False
                    break

            if all_satisfied:
                achieved_level = standard.level
            else:
                break

        db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(
                description_completeness=achieved_level,
                description_completeness_updated_at=datetime.now(tz=timezone.utc),
            )
        )
        db.commit()

        return {"status": "success", "document_id": document_id, "level": achieved_level}


@celery_app.task(name="app.workers.description.recompute_all_stale")
def recompute_all_stale() -> dict:
    """Recompute completeness for all documents not updated in 24 hours."""
    with get_sync_session() as db:
        cutoff = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0)
        docs = db.execute(
            select(Document.id).where(
                (Document.description_completeness_updated_at.is_(None))
                | (Document.description_completeness_updated_at < cutoff)
            )
        ).scalars().all()

    for doc_id in docs:
        recompute_completeness.delay(doc_id)

    logger.info("Queued completeness recomputation for %d documents", len(docs))
    return {"status": "queued", "count": len(docs)}
