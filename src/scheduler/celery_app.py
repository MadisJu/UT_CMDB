import os
import sys
from datetime import timedelta
from pathlib import Path
from src.core.logging_adapter import configure_logging

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

configure_logging()

from src.core.configs.celery_config import celery_app
from src.core.configs.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app.conf.update(
    task_default_queue="ansible",
    timezone="UTC",
)


def _get_schedule_config():
    interval_seconds = None

    try:
        discovery_settings = settings.get_discovery_settings()
        if isinstance(discovery_settings, dict):
            raw = discovery_settings.get("interval_seconds")
            if raw:
                interval_seconds = int(raw)
    except Exception as e:
        logger.warning(f"Could not read interval from discovery_settings: {e}")

    if interval_seconds is None:
        env_value = os.getenv("CMDB_INTERVAL_SECONDS")
        if env_value:
            try:
                interval_seconds = int(env_value)
            except ValueError:
                logger.warning(f"Invalid CMDB_INTERVAL_SECONDS env value: {env_value!r}")

    if interval_seconds is None:
        interval_seconds = int(settings.cmdb_interval_seconds or 3600)

    if interval_seconds <= 0:
        logger.warning(f"Non-positive interval_seconds ({interval_seconds}) -> using default 3600")
        interval_seconds = 3600

    return interval_seconds


interval_seconds = _get_schedule_config()

beat_schedule = {}

beat_schedule["periodic-auto-discovery-sync"] = {
    "task": "src.worker.tasks.auto_discovery.auto_discovery_and_sync",
    "schedule": timedelta(seconds=interval_seconds),
}


celery_app.conf.beat_schedule = beat_schedule

logger.info(f"Configured {len(beat_schedule)} scheduled tasks")
logger.info(f"Auto discovery interval set to {interval_seconds} seconds")


