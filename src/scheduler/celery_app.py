import os
from datetime import timedelta
from celery import Celery
from src.core.services.machine_inventory import MachineInventory
import logging

logger = logging.getLogger(__name__)

# Use memory broker (no external dependencies needed)
broker_url = "memory://"
celery_app = Celery("cmdb_scheduler", broker=broker_url, backend=broker_url)

celery_app.conf.update(
    task_default_queue="ansible",
    timezone="UTC",
)


def _get_schedule_config():
    """Get schedule configuration from machine inventory."""
    try:
        inventory = MachineInventory()
        discovery_settings = inventory.get_discovery_settings()
        
        # Get interval from environment or discovery settings
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", 
                                        discovery_settings.get("interval_seconds", 3600)))
        
        # Get machines for discovery
        machines = inventory.get_enabled_machines()
        
        if not machines:
            logger.warning("No enabled machines found for scheduled discovery")
            return None, None, interval_seconds
        
        # Use first machine as primary target (for backward compatibility)
        primary_machine = machines[0]
        host = primary_machine.get("ip_address") or primary_machine.get("hostname")
        user = primary_machine.get("user") or discovery_settings.get("default_user", "root")
        
        logger.info(f"Scheduled discovery configured for {len(machines)} machines, primary: {host}")
        
        return host, user, interval_seconds
        
    except Exception as e:
        logger.error(f"Failed to get schedule configuration: {e}")
        # Fallback to environment variables
        host = os.getenv("CMDB_HOST", "25.44.45.59")
        user = os.getenv("CMDB_USER", "chronia")
        interval_seconds = int(os.getenv("CMDB_INTERVAL_SECONDS", "3600"))
        return host, user, interval_seconds


# Get schedule configuration
host, user, interval_seconds = _get_schedule_config()

# Configure scheduled tasks
beat_schedule = {}

if host and user:
    # Legacy single-host discovery task
    beat_schedule["periodic-ansible-discovery"] = {
        "task": "worker.tasks.discovery.discovery_task",
        "schedule": timedelta(seconds=interval_seconds),
        "args": [host, user],
    }

# Auto discovery task for all configured machines
beat_schedule["periodic-auto-discovery"] = {
    "task": "worker.tasks.discovery.auto_discovery_task",
    "schedule": timedelta(seconds=interval_seconds),
}

# Linux machines discovery task
beat_schedule["periodic-linux-discovery"] = {
    "task": "worker.tasks.discovery.discovery_by_type_task",
    "schedule": timedelta(seconds=interval_seconds * 2),  # Run every 2 intervals
    "args": ["linux"],
}

celery_app.conf.beat_schedule = beat_schedule

logger.info(f"Configured {len(beat_schedule)} scheduled tasks")


