from celery import Celery

from app.config import settings

celery_app = Celery(
    "hotel_am",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
