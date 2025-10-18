import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL")
backend_url = os.getenv("CELERY_BACKEND_URL")

celery_app = Celery("cmdb", broker=broker_url, backend=backend_url)

celery_app.conf.update(
    task_default_queue="ansible",
    timezone="UTC",
    worker_concurrency=2,
    task_time_limit=600,
)