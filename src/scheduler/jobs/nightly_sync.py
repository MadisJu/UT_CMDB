import json
import os
import uuid
from datetime import datetime, timezone


def get_project_root() -> str:
    current_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(current_dir, "../../.."))


def ensure_queue_directories(queue_root: str) -> None:
    os.makedirs(os.path.join(queue_root, "pending"), exist_ok=True)
    os.makedirs(os.path.join(queue_root, "processing"), exist_ok=True)
    os.makedirs(os.path.join(queue_root, "done"), exist_ok=True)
    os.makedirs(os.path.join(queue_root, "failed"), exist_ok=True)


def atomic_write_json(target_path: str, data: dict) -> None:
    directory = os.path.dirname(target_path)
    os.makedirs(directory, exist_ok=True)
    tmp_path = f"{target_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as tmp_file:
        json.dump(data, tmp_file, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp_path, target_path)


def enqueue_gather_facts_job(host: str, user: str) -> str:
    project_root = get_project_root()
    queue_root = os.path.join(project_root, "queue")
    facts_tree_dir = os.path.join(project_root, "ansible", "fact_cache")

    ensure_queue_directories(queue_root)

    job_id = str(uuid.uuid4())
    today = datetime.now(timezone.utc).date().isoformat()
    idempotency_key = f"gather_facts:{host}:{today}"

    payload = {
        "type": "gather_facts",
        "id": job_id,
        "idempotency_key": idempotency_key,
        "host": host,
        "user": user,
        "modules": ["setup"],
        "options": {"tree_dir": facts_tree_dir},
        "requested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "priority": 0
    }

    pending_dir = os.path.join(queue_root, "pending")
    final_path = os.path.join(pending_dir, f"job-{job_id}.json")

    # Best-effort idempotency: skip if a pending job with same idempotency_key exists
    for name in os.listdir(pending_dir):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(pending_dir, name), "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("idempotency_key") == idempotency_key:
                return os.path.join(pending_dir, name)
        except Exception:
            # Ignore malformed files in pending
            continue

    atomic_write_json(final_path, payload)
    return final_path


if __name__ == "__main__":
    target_host = os.environ.get("CMDB_HOST", "25.44.45.59")
    target_user = os.environ.get("CMDB_USER", "chronia")
    path = enqueue_gather_facts_job(target_host, target_user)
    print(f"Enqueued job at: {path}")


