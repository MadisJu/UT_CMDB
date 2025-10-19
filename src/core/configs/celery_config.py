from celery import Celery
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Use SQLite as broker (proper SQLite database)
broker_url = "sqlalchemy+sqlite:///celery_broker.db"
backend_url = "db+sqlite:///celery_results.db"
celery_app = Celery("cmdb_worker", broker=broker_url, backend=backend_url)

celery_app.conf.update(
    task_default_queue="ansible",
    worker_concurrency=2,
    task_time_limit=600,
)
