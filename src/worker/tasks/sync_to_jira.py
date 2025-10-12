from worker.main import celery_app

# Task for syncing data to JIRA

@celery_app.task(name="worker.tasks.sync_to_jira.sync_task", bind=True, max_retries=3)
def sync_task(self, payload):
    try:
        print(f"uploading to JIRA: {payload}")

        #test
                
        return {"status": "success", "synced_items": len(payload)}
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)