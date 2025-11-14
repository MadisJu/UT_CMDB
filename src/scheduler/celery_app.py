import os
import sys
from datetime import timedelta
from pathlib import Path
from src.core.configs.celery_config import celery_app
from src.core.configs.config import settings
import logging

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

celery_app.conf.update(
    task_default_queue="ansible",
    timezone="UTC",
)


def _get_schedule_config():
    try:
        
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", 
                                        settings.cmdb_interval_seconds or 3600))
        return interval_seconds
        
    except Exception as e:
        logger.error(f"Failed to get schedule configuration: {e}")
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", "3600"))
        return interval_seconds


interval_seconds = _get_schedule_config()

beat_schedule = {}

beat_schedule["periodic-auto-discovery-sync"] = {
    "task": "src.worker.tasks.auto_discovery.auto_discovery_and_sync",
    "schedule": timedelta(seconds=30),
}


celery_app.conf.beat_schedule = beat_schedule

logger.info(f"Configured {len(beat_schedule)} scheduled tasks")



