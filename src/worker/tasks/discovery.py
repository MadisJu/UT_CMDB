import ansible_runner
import json
from worker.main import celery_app

# Task for getting data from Ansible

@celery_app.task(name="worker.tasks.discovery.discovery_task", bind=True, max_retries=3)
def discovery_task(self, host, user):
    try:
        r = ansible_runner.run(
            private_data_dir="/tmp",
            inventory=host,
            module="setup",
            host_pattern="all",
            extravars={"ansible_user": user}
        )
        facts = r.get_fact_cache(host)
        print(json.dumps(facts, indent=2))
        return facts
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)