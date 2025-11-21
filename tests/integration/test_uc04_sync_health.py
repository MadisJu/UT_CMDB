import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
import datetime

class TestUC04SyncHealth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('src.api.routes.jobs.celery_app.control.inspect')
    def test_monitor_sync_health_list_jobs(self, mock_inspect):
        """
        UC-04: IT Administrator views the list of synchronization jobs.
        Current implementation: Returns active/scheduled/reserved jobs.
        """
        # Mock Celery inspector
        mock_inspector = MagicMock()
        mock_inspect.return_value = mock_inspector
        
        # Setup mock data for active tasks
        mock_inspector.active.return_value = {
            "worker1@host": [
                {
                    "id": "task-123",
                    "name": "sync_task",
                    "time_start": datetime.datetime.now().timestamp(),
                    "args": [],
                    "kwargs": {}
                }
            ]
        }
        mock_inspector.scheduled.return_value = {}
        mock_inspector.reserved.return_value = {}

        # Action: Get all jobs
        response = self.client.get("/api/v1/jobs/")

        # Assertions
        self.assertEqual(response.status_code, 200)
        jobs = response.json()
        self.assertTrue(len(jobs) > 0)
        self.assertEqual(jobs[0]['id'], "task-123")
        self.assertEqual(jobs[0]['status'], "running")

    @patch('src.api.routes.jobs.celery_app.AsyncResult')
    def test_monitor_specific_job_status(self, mock_async_result):
        """
        UC-04: IT Administrator selects a specific job for details.
        """
        # Mock a specific task result
        mock_task = MagicMock()
        mock_task.state = 'PROGRESS'
        mock_task.info = {'current': 5, 'total': 10, 'status': 'Processing'}
        mock_async_result.return_value = mock_task

        # Action: Get specific job status
        task_id = "test-task-uuid"
        response = self.client.get(f"/api/v1/jobs/{task_id}")

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['state'], 'PROGRESS')
        self.assertEqual(data['status'], 'Processing')

