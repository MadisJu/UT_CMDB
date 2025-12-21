import unittest
from unittest.mock import MagicMock, patch
from src.core.services.jira_service import JiraService
from src.core.models.asset_model import LinuxAsset, WindowsAsset, HostAsset

class TestJiraService(unittest.TestCase):
    """
    Unit tests for the JiraService.
    Tests the high-level logic for interacting with Jira, including asset querying and creation.
    """

    def setUp(self):
        """Set up the JiraService with a mocked JiraClient."""
        self.mock_jira_client = MagicMock()
        self.service = JiraService(jira_client=self.mock_jira_client)

    def test_get_all_assets(self):
        """Test retrieving all assets using an AQL query."""
        self.mock_jira_client.query_assets.return_value = [{"id": "1", "label": "Asset 1"}]
        assets = self.service.get_all_assets("ObjectType = 'Servers'")
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]["label"], "Asset 1")
        self.mock_jira_client.query_assets.assert_called_once_with("ObjectType = 'Servers'")

    def test_get_asset_schemas(self):
        """Test retrieving asset schemas from Jira."""
        self.mock_jira_client.get_asset_schemas.return_value = {"schemas": []}
        schemas = self.service.get_asset_schemas()
        self.assertEqual(schemas, {"schemas": []})
        self.mock_jira_client.get_asset_schemas.assert_called_once()

    @patch('src.core.services.jira_service.map_linux_to_jira')
    def test_create_asset_from_model_linux(self, mock_map_linux):
        """Test creating a Linux asset in Jira from a LinuxAsset model."""
        mock_map_linux.return_value = {"attributes": []}
        self.mock_jira_client.create_asset.return_value = {"label": "linux-host"}
        asset = LinuxAsset(
            type="linux",
            name="linux-host",
            hostname="linux-host", 
            ipv4_address="1.2.3.4", 
            os="Linux"
        )
        
        result = self.service.create_asset_from_model(asset)
        
        self.assertEqual(result["label"], "linux-host")
        mock_map_linux.assert_called_once_with(asset)

    @patch('src.core.services.jira_service.map_windows_to_jira')
    def test_create_asset_from_model_windows(self, mock_map_windows):
        """Test creating a Windows asset in Jira from a WindowsAsset model."""
        mock_map_windows.return_value = {"attributes": []}
        self.mock_jira_client.create_asset.return_value = {"label": "windows-host"}
        asset = WindowsAsset(
            type="windows",
            name="windows-host",
            hostname="windows-host", 
            ipv4_address="1.2.3.4", 
            os="Windows",
            os_version="10.0",
            installed_updates=[]
        )
        
        result = self.service.create_asset_from_model(asset)
        
        self.assertEqual(result["label"], "windows-host")
        mock_map_windows.assert_called_once_with(asset)

    @patch('src.core.services.jira_service.map_host_to_jira')
    def test_create_asset_from_model_generic(self, mock_map_host):
        """Test creating a generic Host asset in Jira from a HostAsset model."""
        mock_map_host.return_value = {"attributes": []}
        self.mock_jira_client.create_asset.return_value = {"label": "generic-host"}
        asset = HostAsset(
            type="host",
            name="generic-host",
            hostname="generic-host", 
            ipv4_address="1.2.3.4", 
            os="Unknown"
        )
        
        result = self.service.create_asset_from_model(asset)
        
        self.assertEqual(result["label"], "generic-host")
        mock_map_host.assert_called_once_with(asset)

if __name__ == '__main__':
    unittest.main()
