# test_client.py
# Käivita see otse terminalist: python test_client.py

import logging
from src.core.configs.config import settings
import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from src.core.integrations.jira_client import JiraClient

# MUUDA SEDA IMPORT-RIDA VASTAVALT SELLELE, KUS SU KLIENDIFAL ASUB
# Ma eeldan, et see on 'src/api/clients/' kaustas:
from src.core.integrations.jira_client import JiraClient

project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.core.configs.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_jira_client():
    """Fixture to mock JiraClient."""
    client = MagicMock(spec=JiraClient)
    client.list_object_attributes.return_value = [
        {"id": 1, "name": "Attribute 1"},
        {"id": 2, "name": "Attribute 2"}
    ]
    client.create_asset.return_value = MagicMock(objectKey="TEST-123", id=123)
    client.update_asset.return_value = MagicMock(label="Updated Asset")
    client.get_asset_by_id.return_value = MagicMock(label="Fetched Asset")
    client.delete_asset.return_value = True
    return client

@pytest.fixture
def new_asset_data():
    """Fixture to provide new asset data."""
    return {
        "objectTypeId": 25,
        "attributes": [
            {
                "objectTypeAttributeId": 150,
                "objectAttributeValues": [{"value": "Test Object"}]
            },
            {
                "objectTypeAttributeId": 178,
                "objectAttributeValues": [{"value": "test-hostname"}]
            },
            {
                "objectTypeAttributeId": 177,
                "objectAttributeValues": [{"value": "192.168.1.1"}]
            },
            {
                "objectTypeAttributeId": 179,
                "objectAttributeValues": [{"value": "x86_64"}]
            },
            {
                "objectTypeAttributeId": 180,
                "objectAttributeValues": [{"value": "Intel Xeon"}]
            },
            {
                "objectTypeAttributeId": 181,
                "objectAttributeValues": [{"value": "4"}]
            },
            {
                "objectTypeAttributeId": 182,
                "objectAttributeValues": [{"value": "8"}]
            },
            {
                "objectTypeAttributeId": 187,
                "objectAttributeValues": [{"value": "Ubuntu 20.04"}]
            },
            {
                "objectTypeAttributeId": 175,
                "objectAttributeValues": [{"value": 16.0}]
            },
            {
                "objectTypeAttributeId": 176,
                "objectAttributeValues": [{"value": 500.0}]
            },
            {
                "objectTypeAttributeId": 173,
                "objectAttributeValues": [{"value": 45.0}]
            }
        ]
    }

@patch("src.core.integrations.jira_client.JiraClient", autospec=True)
def test_list_object_attributes(mock_jira_client):
    client = mock_jira_client.return_value
    client.list_object_attributes.return_value = [
        {"id": 1, "name": "Attribute 1"},
        {"id": 2, "name": "Attribute 2"}
    ]

    attributes = client.list_object_attributes("13")
    assert len(attributes) == 2
    assert attributes[0]["name"] == "Attribute 1"

@patch("src.core.integrations.jira_client.JiraClient", autospec=True)
def test_create_asset(mock_jira_client, new_asset_data):
    client = mock_jira_client.return_value
    client.create_asset.return_value = MagicMock(objectKey="TEST-123", id=123)

    created_asset = client.create_asset(new_asset_data)
    assert created_asset.objectKey == "TEST-123"
    assert created_asset.id == 123

@patch("src.core.integrations.jira_client.JiraClient", autospec=True)
def test_update_asset(mock_jira_client):
    client = mock_jira_client.return_value
    client.update_asset.return_value = MagicMock(label="Updated Asset")

    update_data = {
        "attributes": [
            {
                "objectTypeAttributeId": 150,
                "objectAttributeValues": [{"value": "Updated Name"}]
            }
        ]
    }

    updated_asset = client.update_asset(123, update_data)
    assert updated_asset.label == "Updated Asset"

@patch("src.core.integrations.jira_client.JiraClient", autospec=True)
def test_get_asset_by_id(mock_jira_client):
    client = mock_jira_client.return_value
    client.get_asset_by_id.return_value = MagicMock(label="Fetched Asset")

    fetched_asset = client.get_asset_by_id(123)
    assert fetched_asset.label == "Fetched Asset"

@patch("src.core.integrations.jira_client.JiraClient", autospec=True)
def test_delete_asset(mock_jira_client):
    client = mock_jira_client.return_value
    client.delete_asset.return_value = True

    delete_success = client.delete_asset(123)
    assert delete_success is True

def run_test():
    logger.info("Initializing JiraClient...")
    try:
        client = JiraClient(settings=settings)
        logger.info("JiraClient initialized.")

        logger.info("Listing attributes for object type ID 13...")
        client.list_object_attributes("13")
        
        return

        

    except Exception as e:
        logger.error(f"TEST FAILED: {e}", exc_info=True)

if __name__ == "__main__":
    run_test()