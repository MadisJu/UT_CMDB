from src.core.configs.celery_config import celery_app

# Import all task modules to register them
from src.worker.tasks import discovery, sync_to_jira, auto_discovery

# This ensures all tasks are registered with Celery
__all__ = ['celery_app']

