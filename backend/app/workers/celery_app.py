"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "adms",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.ocr.*": {"queue": "ocr"},
        "app.workers.llm.*": {"queue": "llm"},
        "app.workers.ingest.*": {"queue": "ingest"},
        "app.workers.fixity.*": {"queue": "fixity"},
        "app.workers.export.*": {"queue": "export"},
    },
    beat_schedule={
        "fixity-check-weekly": {
            "task": "app.workers.fixity.run_scheduled_fixity",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),
        },
        "poll-watch-folders": {
            "task": "app.workers.ingest.poll_watch_folders",
            "schedule": 60.0,
        },
        "recompute-completeness-nightly": {
            "task": "app.workers.description.recompute_all_stale",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

celery_app.autodiscover_tasks([
    "app.workers.ocr",
    "app.workers.llm",
    "app.workers.ingest",
    "app.workers.fixity",
    "app.workers.export",
    "app.workers.description",
    "app.workers.thumbnails",
])
