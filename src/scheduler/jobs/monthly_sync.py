from scheduler.celery_app import celery_app 

#see ka suht placeholder

if __name__ == "__main__":
    print("Start Celery beat with:\n"
          "  PYTHONPATH=. "
          "python3 -m celery -A src.scheduler.jobs.monthly_sync beat -l info")