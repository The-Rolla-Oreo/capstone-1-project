from celery import Celery
from kombu import Queue
from .settings import get_settings

settings = get_settings()

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    # skipcq: PYL-W0069
    #backend=settings.CELERY_RESULT_BACKEND, # Don't need to keep track of results
    include=["backend.celery_worker"],
)

celery_app.conf.update(
    task_track_started=True,
)

# Use unique, auto-deleting queues for each developer in dev mode
if settings.DEV_MODE:
    developer_queue = f"dev_{settings.DEV_USER}"

    # Define a non-durable, auto-deleting queue for the developer
    celery_app.conf.task_queues = (
        Queue(developer_queue, durable=False, auto_delete=True),
    )

    # Set the default queue for this worker
    celery_app.conf.task_default_queue = developer_queue

    # Route all tasks to this developer's queue
    celery_app.conf.task_routes = {
        'backend.celery_worker.*': {'queue': developer_queue}
    }
