"""Named Entity Recognition (NER) Celery tasks using spaCy.

Extracts persons, organizations, locations, and dates from OCR text.
All suggestions require human review — never auto-applied.
"""

import logging
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models.authority_record import AuthorityRecord
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.location import Location
from app.models.preservation_event import PreservationEvent
from app.models.review_queue import ReviewQueue
from app.models.system_setting import SystemSetting
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_sync_session() -> Session:
    engine = create_engine(settings.sync_database_url)
    return Session(engine)


def _get_ner_settings(db: Session) -> dict:
    """Load NER configuration from system_settings."""
    defaults = {
        "enabled": False,
        "run_after_ocr": False,
        "entity_types": ["PERSON", "ORG", "GPE", "LOC", "DATE"],
        "suggest_authority": True,
        "suggest_geolocation": True,
        "suggest_tags": True,
        "require_review": True,
        "model": "en_core_web_lg",
    }
    for key in defaults:
        setting = db.execute(
            select(SystemSetting).where(SystemSetting.key == f"ner.{key}")
        ).scalar_one_or_none()
        if setting and setting.value is not None:
            defaults[key] = setting.value.get("value", defaults[key])
    return defaults


def _fuzzy_match_authority(db: Session, name: str, threshold: float = 0.85) -> AuthorityRecord | None:
    """Find a fuzzy-matching authority record by name."""
    from difflib import SequenceMatcher

    records = db.execute(
        select(AuthorityRecord).where(AuthorityRecord.authorized_name.isnot(None))
    ).scalars().all()

    best_match = None
    best_ratio = 0.0

    for record in records:
        ratio = SequenceMatcher(None, name.lower(), record.authorized_name.lower()).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = record

    return best_match


def _fuzzy_match_location(db: Session, name: str, threshold: float = 0.85) -> Location | None:
    """Find a fuzzy-matching location record by name."""
    from difflib import SequenceMatcher

    records = db.execute(
        select(Location).where(Location.authorized_name.isnot(None))
    ).scalars().all()

    best_match = None
    best_ratio = 0.0

    for record in records:
        ratio = SequenceMatcher(None, name.lower(), record.authorized_name.lower()).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = record

    return best_match


def _geocode_location(place_name: str) -> dict | None:
    """Attempt to geocode a place name via Nominatim (server-side)."""
    import httpx

    try:
        resp = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place_name, "format": "json", "limit": 1},
            headers={"User-Agent": "ADMS/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return {
                "latitude": float(results[0]["lat"]),
                "longitude": float(results[0]["lon"]),
                "display_name": results[0].get("display_name", place_name),
            }
    except Exception as e:
        logger.warning("Geocoding failed for '%s': %s", place_name, e)

    return None


@celery_app.task(name="app.workers.ner.process_document", bind=True)
def process_document(self, document_id: int) -> dict:
    """Run NER on a document's OCR text and generate suggestions."""
    with get_sync_session() as db:
        ner_settings = _get_ner_settings(db)

        if not ner_settings["enabled"]:
            return {"status": "skipped", "reason": "NER disabled"}

        document = db.execute(
            select(Document).where(Document.id == document_id)
        ).scalar_one_or_none()

        if not document:
            return {"status": "error", "message": "Document not found"}

        # Concatenate OCR text from all files/pages
        files = db.execute(
            select(DocumentFile).where(
                DocumentFile.document_id == document_id,
                DocumentFile.ocr_status == "complete",
            )
        ).scalars().all()

        ocr_text = "\n".join(f.ocr_text for f in files if f.ocr_text)
        if not ocr_text.strip():
            return {"status": "skipped", "reason": "No OCR text available"}

        try:
            import spacy

            model_name = ner_settings["model"]
            nlp = spacy.load(model_name)
        except Exception as e:
            logger.error("Failed to load spaCy model '%s': %s", ner_settings["model"], e)
            return {"status": "error", "message": f"spaCy model load failed: {e}"}

        try:
            # Run NER
            doc_nlp = nlp(ocr_text[:100000])  # Limit text length for performance

            enabled_types = set(ner_settings["entity_types"])
            entity_counts: Counter = Counter()
            unique_entities: dict[tuple[str, str], list[str]] = {}

            for ent in doc_nlp.ents:
                if ent.label_ not in enabled_types:
                    continue

                key = (ent.label_, ent.text.strip())
                entity_counts[key] += 1

                if key not in unique_entities:
                    unique_entities[key] = []

                # Store sample contexts (first 3 occurrences)
                if len(unique_entities[key]) < 3:
                    start = max(0, ent.start_char - 50)
                    end = min(len(ocr_text), ent.end_char + 50)
                    unique_entities[key].append(ocr_text[start:end])

            # Build suggestions
            suggestions: list[dict] = []

            for (ent_type, ent_text), contexts in unique_entities.items():
                count = entity_counts[(ent_type, ent_text)]
                suggestion: dict = {
                    "entity_text": ent_text,
                    "entity_type": ent_type,
                    "occurrences": count,
                    "sample_contexts": contexts,
                    "actions": [],
                }

                if ent_type in ("PERSON", "ORG") and ner_settings["suggest_authority"]:
                    match = _fuzzy_match_authority(db, ent_text)
                    if match:
                        suggestion["actions"].append({
                            "type": "link_authority",
                            "authority_id": match.id,
                            "authority_name": match.authorized_name,
                            "match_confidence": "high",
                        })
                    else:
                        suggestion["actions"].append({
                            "type": "create_authority",
                            "proposed_name": ent_text,
                            "entity_type": "person" if ent_type == "PERSON" else "organization",
                        })
                        # Create pending authority record
                        new_authority = AuthorityRecord(
                            entity_type="person" if ent_type == "PERSON" else "organization",
                            authorized_name=ent_text,
                            created_by_ner=True,
                            created_by=None,
                        )
                        db.add(new_authority)
                        db.flush()
                        suggestion["actions"][-1]["authority_id"] = new_authority.id

                elif ent_type in ("GPE", "LOC"):
                    match = _fuzzy_match_location(db, ent_text)
                    if match:
                        suggestion["actions"].append({
                            "type": "link_location",
                            "location_id": match.id,
                            "location_name": match.authorized_name,
                            "match_confidence": "high",
                        })
                    elif ner_settings["suggest_geolocation"]:
                        geo = _geocode_location(ent_text)
                        if geo:
                            suggestion["actions"].append({
                                "type": "create_location",
                                "proposed_name": ent_text,
                                "geo_latitude": geo["latitude"],
                                "geo_longitude": geo["longitude"],
                                "display_name": geo["display_name"],
                            })
                        else:
                            suggestion["actions"].append({
                                "type": "create_location",
                                "proposed_name": ent_text,
                            })

                if ner_settings["suggest_tags"]:
                    suggestion["actions"].append({
                        "type": "add_tag",
                        "tag_text": ent_text,
                    })

                suggestions.append(suggestion)

            # Store suggestions in document
            existing_suggestions = document.llm_suggestions or {}
            existing_suggestions["ner"] = {
                "entities": suggestions,
                "model": ner_settings["model"],
                "processed_at": datetime.now(tz=timezone.utc).isoformat(),
                "total_entities": len(suggestions),
            }

            db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(llm_suggestions=existing_suggestions)
            )

            # Add to review queue
            if ner_settings["require_review"] and suggestions:
                db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(review_status="pending")
                )
                existing_review = db.execute(
                    select(ReviewQueue).where(ReviewQueue.document_id == document_id)
                ).scalar_one_or_none()
                if not existing_review:
                    db.add(ReviewQueue(
                        document_id=document_id,
                        reason="llm_suggestions",
                        priority="normal",
                        notes=f"NER extracted {len(suggestions)} entities",
                    ))

            # Log preservation event
            db.add(PreservationEvent(
                document_id=document_id,
                event_type="ocr",
                event_outcome="success",
                event_detail=(
                    f"NER completed with spaCy {ner_settings['model']}. "
                    f"Extracted {len(suggestions)} unique entities."
                ),
                agent="celery_worker:ner",
            ))

            db.commit()

            logger.info(
                "NER completed for document %d: %d entities extracted",
                document_id, len(suggestions),
            )
            return {
                "status": "success",
                "document_id": document_id,
                "entities_found": len(suggestions),
            }

        except Exception as e:
            logger.error("NER failed for document %d: %s", document_id, e)
            db.add(PreservationEvent(
                document_id=document_id,
                event_type="ocr",
                event_outcome="failure",
                event_detail=f"NER failed: {e}",
                agent="celery_worker:ner",
            ))
            db.commit()
            return {"status": "error", "message": str(e)}
