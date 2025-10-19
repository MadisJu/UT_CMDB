from worker.main import celery_app
from worker.tasks.discovery import discovery_task
from worker.tasks.sync_to_jira import sync_task
from scheduler.celery_app import celery_app


#result = discovery_task.delay("25.44.45.59", "chronia")
#result = sync_task.delay([{"id": 123, "name": "test asset"}])
result = celery_app.send_task('worker.tasks.discovery.discovery_task')


print(result.status)


