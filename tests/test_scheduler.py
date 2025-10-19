"""Simple smoke tests for the scheduler configuration."""

from pathlib import Path
import sys

# Ensure the project root is on sys.path so ``src`` can be imported when
# pytest runs from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scheduler.celery_app import celery_app


def test_scheduler_has_configured_tasks():
    """Scheduler should define at least one beat schedule entry."""
    schedule = getattr(celery_app.conf, "beat_schedule", {})

    assert isinstance(schedule, dict), "beat_schedule must be a mapping"
    assert schedule, "Scheduler beat schedule is empty"


def test_each_schedule_entry_defines_task():
    """Every configured schedule entry must declare the Celery task name."""
    schedule = getattr(celery_app.conf, "beat_schedule", {})

    missing_task = [name for name, entry in schedule.items() if not entry.get("task")]

    assert not missing_task, f"Schedule entries missing task: {missing_task}"

