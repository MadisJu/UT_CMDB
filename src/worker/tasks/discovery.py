import ansible_runner
import json
from worker.main import celery_app
import requests
from worker.tasks.sync_to_jira import sync_task

api_url = "http://localhost:8000/discovery/results"

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

        # CPU info kättesaamine Ansiblest
        cpu_info = {
            "architecture": facts.get("ansible_architecture"),
            "processor": facts.get("ansible_processor"),
            "physical_cpus": facts.get("ansible_processor_count"),
            "virtual_cpus": facts.get("ansible_processor_vcpus"),
        }
        
        sync_task.delay(cpu_info, self.request.id)

        return facts
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)