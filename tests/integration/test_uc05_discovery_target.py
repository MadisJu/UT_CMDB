import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes.discovery import get_machine_inventory

class TestUC05DiscoveryTarget(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
        # Override the MachineInventory dependency to avoid file system checks
        self.mock_inventory = MagicMock()
        self.mock_inventory.get_all_machines.return_value = ["host1", "host2"]
        app.dependency_overrides[get_machine_inventory] = lambda: self.mock_inventory

    def tearDown(self):
        app.dependency_overrides = {}

    @patch('src.api.routes.discovery.auto_discovery_task')
    @patch('src.api.routes.discovery.sync_discovered_assets')
    def test_add_discovery_target_auto(self, mock_sync, mock_discovery):
        """
        UC-05: Administrator wants to discover servers.
        Current implementation: Triggers 'auto' discovery which scans known inventory.
        This test verifies the triggering mechanism works.
        """
        # Mock the chain construction
        mock_chain = MagicMock()
        # Simulate the chain (task | task)
        mock_discovery.s.return_value = MagicMock()
        mock_sync.s.return_value = MagicMock()
        
        # The pipe operator logic in python for celery chains
        mock_discovery.s.return_value.__or__.return_value = mock_chain
        
        mock_task_instance = MagicMock()
        mock_task_instance.id = "new-job-uuid"
        mock_chain.apply_async.return_value = mock_task_instance

        # Action: Start auto discovery
        response = self.client.post("/api/v1/auto")

        # Assertions
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn("job_id", data)
        self.assertEqual(data['message'], "Auto discovery and Jira sync job has been started.")
