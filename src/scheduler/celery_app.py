import os
from datetime import timedelta
from celery import Celery


# Broker/Backend
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("cmdb_scheduler", broker=broker_url, backend=broker_url)

# Ensure tasks are published to the same queue the worker consumes
celery_app.conf.update(
    task_default_queue="ansible",
    timezone="UTC",
)


def _get_schedule_config():
    host = os.getenv("CMDB_HOST", "25.44.45.59")
    user = os.getenv("CMDB_USER", "chronia")
    interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", "3600"))
    # Pass raw host to worker; worker decides how to interpret inventory
    inventory = host
    return inventory, user, interval_seconds


inventory, user, interval_seconds = _get_schedule_config()

celery_app.conf.beat_schedule = {
    "periodic-ansible-discovery": {
        "task": "worker.tasks.discovery.discovery_task",
        "schedule": timedelta(seconds=interval_seconds),
        "args": [inventory, user],
    }
}


