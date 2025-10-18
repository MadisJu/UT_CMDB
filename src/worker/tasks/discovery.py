import ansible_runner
import json
from worker.main import celery_app
import requests

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
        print(json.dumps(facts, indent=2))

        payload = {
            "assets": facts,  
            "job_id": self.request.id
        }
        
        response = requests.post(api_url, json=payload)
        response.raise_for_status() 
        
        print(response.json())
        return facts
    
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)