import os
import sys
from datetime import timedelta
from pathlib import Path
from src.core.configs.celery_config import celery_app
from src.core.services.machine_inventory import MachineInventory
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
        inventory = MachineInventory()
        discovery_settings = inventory.get_discovery_settings()
        
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", 
                                        discovery_settings.get("interval_seconds", 3600)))
        
        machines = inventory.get_enabled_machines()
        
        if not machines:
            logger.warning("No enabled machines found for scheduled discovery")
            return None, None, interval_seconds
        
        primary_machine = machines[0]
        host = primary_machine.get("ip_address") or primary_machine.get("hostname")
        user = primary_machine.get("user") or discovery_settings.get("default_user", "root")
        
        logger.info(f"Scheduled discovery configured for {len(machines)} machines, primary: {host}")
        
        return host, user, interval_seconds
        
    except Exception as e:
        logger.error(f"Failed to get schedule configuration: {e}")
        host = os.getenv("CMDB_HOST", "25.44.45.59")
        user = os.getenv("CMDB_USER", "chronia")
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", "3600"))
        return host, user, interval_seconds


host, user, interval_seconds = _get_schedule_config()

beat_schedule = {}

if host and user:
    beat_schedule["periodic-ansible-discovery"] = {
        "task": "src.worker.tasks.discovery.discovery_task",
        "schedule": timedelta(seconds=interval_seconds),
        "args": [host, user],
    }

beat_schedule["periodic-auto-discovery"] = {
    "task": "src.worker.tasks.auto_discovery.auto_discovery_task",
    "schedule": timedelta(seconds=interval_seconds),
}

beat_schedule["periodic-linux-discovery"] = {
    "task": "src.worker.tasks.auto_discovery.discovery_by_type_task",
    "schedule": timedelta(seconds=interval_seconds * 2),
    "args": ["linux"],
}

celery_app.conf.beat_schedule = beat_schedule

logger.info(f"Configured {len(beat_schedule)} scheduled tasks")



