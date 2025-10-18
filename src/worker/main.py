from celery import Celery
import os
from celery.schedules import crontab

# Use memory broker (no external dependencies needed)
broker_url = "memory://"
celery_app = Celery("cmdb_worker", broker=broker_url, backend=broker_url)

celery_app.conf.update(
    task_default_queue="ansible",
    worker_concurrency=2,
    task_time_limit=600,
)

# Import all task modules to register them
from worker.tasks.discovery import discovery_task, batch_discovery_task
from worker.tasks.sync_to_jira import sync_task, sync_discovered_assets
from worker.tasks.auto_discovery import auto_discovery_task, discovery_by_type_task

