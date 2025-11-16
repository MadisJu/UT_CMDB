# scheduleri jaoks unit testid

import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture()
def mock_celery_app():
    celery_app = MagicMock()
    celery_app.conf.beat_schedule = {
        "periodic-ansible-discovery": {
            "task": "worker.tasks.discovery.discovery_task",
            "schedule": 60.0,
        },
        "periodic-auto-discovery": {
            "task": "worker.tasks.discovery.auto_discovery_task",
            "schedule": 120.0,
        },
        "periodic-linux-discovery": {
            "task": "worker.tasks.discovery.discovery_by_type_task",
            "schedule": 180.0,
        },
    }
    return celery_app

def test_scheduler_configures_expected_tasks(mock_celery_app):
    schedule = mock_celery_app.conf.beat_schedule

    assert schedule, "Scheduler beat schedule should not be empty"
    assert schedule["periodic-ansible-discovery"]["task"] == "worker.tasks.discovery.discovery_task"
    assert schedule["periodic-auto-discovery"]["task"] == "worker.tasks.discovery.auto_discovery_task"
    assert schedule["periodic-linux-discovery"]["task"] == "worker.tasks.discovery.discovery_by_type_task"

def test_scheduler_send_task_called(mock_celery_app):
    beat_schedule = mock_celery_app.conf.beat_schedule
    periodic = beat_schedule["periodic-ansible-discovery"]

    with patch.object(mock_celery_app, "send_task") as mock_send_task:
        mock_celery_app.send_task(periodic["task"], args=periodic.get("args", []))

        mock_send_task.assert_called_once_with(
            "worker.tasks.discovery.discovery_task",
            args=periodic.get("args", []),
        )

