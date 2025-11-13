from celery import Celery
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / "src" / "core" / "configs" / ".env")

from src.core.configs.config import settings
broker_url = settings.celery_broker_url
backend_url = settings.celery_result_backend

celery_app = Celery("cmdb_worker", broker=broker_url, backend=backend_url)

celery_app.conf.update(
    task_default_queue="ansible",
    worker_concurrency=2,
    task_time_limit=600,
    include=[
        'src.worker.tasks.discovery',
        'src.worker.tasks.auto_discovery',
        'src.worker.tasks.sync_to_jira',
    ]
)
