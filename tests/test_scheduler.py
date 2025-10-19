"""Unit tests for scheduler configuration without live Celery services."""

from pathlib import Path
import sys
from unittest.mock import patch

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture()
def scheduler_module():
    """Import and reload the scheduler module for each test."""
    import importlib

    for module in ["src.scheduler.celery_app", "src.scheduler"]:
        sys.modules.pop(module, None)

    module = importlib.import_module("src.scheduler.celery_app")
    yield module

    for module in ["src.scheduler.celery_app", "src.scheduler"]:
        sys.modules.pop(module, None)


def test_scheduler_configures_expected_tasks(scheduler_module):
    """Importing the scheduler module should populate the beat schedule."""
    celery_app = scheduler_module.celery_app
    schedule = celery_app.conf.beat_schedule

    assert schedule, "Scheduler beat schedule should not be empty"
    assert schedule["periodic-ansible-discovery"]["task"] == "worker.tasks.discovery.discovery_task"
    assert schedule["periodic-auto-discovery"]["task"] == "worker.tasks.discovery.auto_discovery_task"
    assert schedule["periodic-linux-discovery"]["task"] == "worker.tasks.discovery.discovery_by_type_task"


def test_scheduler_send_task_called(scheduler_module):
    """Verify that executing a scheduled entry sends the expected task."""
    celery_app = scheduler_module.celery_app
    beat_schedule = celery_app.conf.beat_schedule

    periodic = beat_schedule["periodic-ansible-discovery"]

    with patch.object(celery_app, "send_task") as mock_send_task:
        celery_app.send_task(periodic["task"], args=periodic.get("args", []))

        mock_send_task.assert_called_once_with(
            "worker.tasks.discovery.discovery_task",
            args=periodic.get("args", []),
        )

