from src.core.configs.celery_config import celery_app

# Import all task modules to register them
from src.worker.tasks.discovery import discovery_task, batch_discovery_task
from src.worker.tasks.sync_to_jira import sync_task, sync_discovered_assets
from src.worker.tasks.auto_discovery import auto_discovery_task, discovery_by_type_task

