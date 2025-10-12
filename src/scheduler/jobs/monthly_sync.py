import os
import time
from .nightly_sync import enqueue_gather_facts_job


def run_scheduler_loop(host: str, user: str, interval_seconds: int) -> None:
    while True:
        path = enqueue_gather_facts_job(host, user)
        print(f"Enqueued: {path}")
        time.sleep(max(1, interval_seconds))


if __name__ == "__main__":
    target_host = os.environ.get("CMDB_HOST", "25.44.45.59")
    target_user = os.environ.get("CMDB_USER", "chronia")
    interval = int(os.environ.get("CMDB_INTERVAL_SECONDS", "3600"))
    run_scheduler_loop(target_host, target_user, interval)