from worker.main import celery_app
from worker.tasks.discovery import discovery_task
from worker.tasks.sync_to_jira import sync_task


#result = discovery_task.delay("25.44.45.59", "chronia")
result = sync_task.delay([{"id": 123, "name": "test asset"}])

print(result.status)