from scheduler.celery_app import celery_app  # noqa: F401

# This module only needs to import the scheduler Celery app so that
# `celery -A src.scheduler.jobs.monthly_sync beat` can discover the beat schedule
# defined in `src/scheduler/celery_app.py`.

if __name__ == "__main__":
    print("Start Celery beat with:\n"
          "  PYTHONPATH=. CELERY_BROKER_URL=redis://localhost:6379/0 "
          "python3 -m celery -A src.scheduler.jobs.monthly_sync beat -l info")