from celery import Celery
import os
from celery.schedules import crontab

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("cmdb_worker", broker=broker_url, backend=broker_url)

celery_app.conf.update(
    task_default_queue="ansible",
    worker_concurrency=2,
    task_time_limit=600,
)

from worker.tasks.discovery import discovery_task
from worker.tasks.sync_to_jira import sync_task

