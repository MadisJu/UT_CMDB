from main import celery_app


from worker.tasks.discovery import discovery_task
from worker.tasks.sync_to_jira import sync_task

