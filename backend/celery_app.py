from celery import Celery
from .settings import get_settings

settings = get_settings()

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.celery_worker"],
)

celery_app.conf.update(
    task_track_started=True,
)
