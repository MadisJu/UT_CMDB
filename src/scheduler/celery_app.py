import os
from datetime import timedelta
from celery import Celery
from dotenv import load_dotenv
from main import celery_app

load_dotenv()

def _get_schedule_config():
    host = os.getenv("CMDB_HOST", "25.44.45.59")
    user = os.getenv("CMDB_USER", "chronia")
    interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", "3600"))
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


