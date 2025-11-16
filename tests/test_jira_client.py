import unittest
from unittest.mock import patch, MagicMock
import os
from src.core.integrations.jira_client import JiraClient
from src.core.configs.config import Settings

class TestJiraClient(unittest.TestCase):

    def setUp(self):
        """Set up a mock settings object for testing."""
        self.mock_settings = Settings(
            jira_user_email="test@example.com",
            jira_api_token="test_token",
            jira_cloud_id="test_cloud_id",
            jira_asset_workspace_id="test_workspace_id"
        )
        self.client = JiraClient(settings=self.mock_settings)

    def test_initialization_success(self):
        """Test that the JiraClient initializes correctly with valid settings."""
        self.assertEqual(self.client.email, "test@example.com")
        self.assertEqual(self.client.token, "test_token")
        self.assertIsNotNone(self.client.auth)

    def test_initialization_failure_missing_settings(self):
        """Test that JiraClient raises ValueError if settings are missing."""
        with self.assertRaises(ValueError):
            JiraClient(settings=Settings())

    @patch('requests.get')
    def test_query_assets_success(self, mock_get):
        """Test successful asset querying."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "objectEntries": [{
                "id": "1", 
                "label": "Test Asset",
                "objectKey": "TEST-1",
                "attributes": []
            }]
        }
        mock_get.return_value = mock_response

        assets = self.client.query_assets("ObjectType = 'Servers'")
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].label, "Test Asset")
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_asset_by_id_success(self, mock_get):
        """Test successfully getting an asset by its ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "1",
            "objectKey": "KEY-1",
            "label": "Test Asset",
            "objectType": {"id": "25", "name": "Servers"},
            "created": "2024-01-01T00:00:00.000Z",
            "updated": "2024-01-01T00:00:00.000Z",
            "hasAvatar": False,
            "timestamp": "2024-01-01T00:00:00.000Z",
            "attributes": []
        }
        mock_get.return_value = mock_response

        asset = self.client.get_asset_by_id("1")
        self.assertEqual(asset.id, "1")
        self.assertEqual(asset.label, "Test Asset")
        mock_get.assert_called_with(
            f"{self.client.base_url}/object/1",
            headers=self.client.headers,
            auth=self.client.auth
        )

    @patch('requests.delete')
    def test_delete_asset_success(self, mock_delete):
        """Test successful asset deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 204  # No content on successful deletion
        mock_delete.return_value = mock_response

        result = self.client.delete_asset("1")
        self.assertTrue(result)
        mock_delete.assert_called_with(
            f"{self.client.base_url}/object/1",
            headers=self.client.headers,
            auth=self.client.auth
        )

if __name__ == '__main__':
    unittest.main()
