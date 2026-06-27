"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery = Celery(
    "scoreforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,  # 60 seconds max per task
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
