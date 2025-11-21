import unittest
import json
import os
from unittest.mock import patch, MagicMock
from src.core.services.jira_field_mapper_service import JiraFieldMapper
from src.core.models.asset_model import LinuxAsset

class TestUC06AttributeMapping(unittest.TestCase):
    def setUp(self):
        # Create a temporary mapping file
        self.test_map_file = "tests/temp_jira_map.json"
        self.initial_map = {
            "server.hostname": "10001",
            "linux.distro": "10002"
        }
        with open(self.test_map_file, 'w') as f:
            json.dump(self.initial_map, f)

    def tearDown(self):
        if os.path.exists(self.test_map_file):
            os.remove(self.test_map_file)

    @patch('src.core.services.jira_field_mapper_service.JiraClient')
    def test_configure_attribute_mapping_load_and_map(self, MockJiraClient):
        """
        UC-06: System maps internal fields to Asset Manager attributes.
        Verifies that the mapper reads the configuration and applies it correctly.
        """
        # Setup
        mapper = JiraFieldMapper(mapping_file=self.test_map_file)
        
        # Create a test asset
        asset = LinuxAsset(
            hostname="test-host",
            type="linux",
            name="test-host",
            distro="Ubuntu"
        )

        # Action: Map the asset
        # We verify the mapping logic uses the IDs from our config file
        result = mapper.map_asset(asset)

        # Assertions
        attributes = result['attributes']
        
        # Find the attribute for hostname (should be 10001)
        hostname_attr = next((a for a in attributes if a['objectTypeAttributeId'] == "10001"), None)
        self.assertIsNotNone(hostname_attr, "Hostname mapping not found using ID 10001")
        self.assertEqual(hostname_attr['objectAttributeValues'][0]['value'], "test-host")

        # Find the attribute for distro (should be 10002)
        distro_attr = next((a for a in attributes if a['objectTypeAttributeId'] == "10002"), None)
        self.assertIsNotNone(distro_attr, "Distro mapping not found using ID 10002")
        self.assertEqual(distro_attr['objectAttributeValues'][0]['value'], "Ubuntu")

    @patch('src.core.services.jira_field_mapper_service.JiraClient')
    def test_mapping_persistence(self, MockJiraClient):
        """
        UC-06: New mappings are saved to persistent storage.
        """
        # Configure mock to return a dict with ID when create_attribute is called
        mock_client_instance = MockJiraClient.return_value
        mock_client_instance.create_attribute.return_value = {"id": "99999"}

        mapper = JiraFieldMapper(mapping_file=self.test_map_file)
        
        # Simulate ensuring a new attribute which triggers a save
        # We manually update the internal map and save, simulating the 'ensure_attribute' flow
        mapper.field_map["server.new_field"] = "99999"
        mapper.save_mapping()

        # Read the file back to verify persistence
        with open(self.test_map_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["server.new_field"], "99999")

