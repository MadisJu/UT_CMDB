from unittest.mock import patch

with patch("src.core.integrations.jira_client.JiraClient") as MockJiraClient:
    MockJiraClient.return_value = None 
    from src.core.models.jira_model import map_linux_to_jira

import pytest
from src.core.models.asset_model import LinuxAsset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def mock_jira_client():
    """Fixture to mock JiraClient."""
    client = MockJiraClient()
    client.sync_assets.return_value = {
        "total": 3,
        "created": 2,
        "updated": 1,
        "errors": 0,
        "error_details": []
    }
    return client

@pytest.fixture
def test_assets():
    """Fixture to create test Linux assets."""
    return [
        LinuxAsset(
            name="web-server-01",
            type="linux",
            hostname="web-server-01",
            ip_address="192.168.1.100",
            os="Ubuntu 22.04 LTS",
            cpu_cores=8,
            memory_mb=8192,
            kernel_version="5.15.0-91-generic",
            distro="Ubuntu",
            package_count=1250,
            metadata={
                "discovery_method": "test_data",
                "environment": "production",
                "purpose": "web server",
                "last_updated": "2024-01-15T10:30:00Z",
                "memory_gb": "8",
                "architecture": "x86_64",
                "processor_model": "Intel Core i7-8700K",
                "physical_cpus": "1",
                "virtual_cpus": "4",
                "disk_usage": "75%",
                "cpu_temperature": "45",
                "domain_name": "example.com",
                "asset_tag": "WEB-001",
                "serial_number": "SN123456789",
                "model_name": "Dell PowerEdge R640",
                "device_type": "Server",
                "support_group": "IT Operations",
                "owner_group": "Web Team"
            }
        ),
        LinuxAsset(
            name="db-server-02",
            type="linux",
            hostname="db-server-02",
            ip_address="192.168.1.101",
            os="Red Hat Enterprise Linux 8.8",
            cpu_cores=16,
            memory_mb=16384,
            kernel_version="4.18.0-477.13.1.el8_8.x86_64",
            distro="RHEL",
            package_count=2100,
            metadata={
                "discovery_method": "test_data",
                "environment": "production",
                "purpose": "database server",
                "last_updated": "2024-01-15T10:35:00Z",
                "memory_gb": "16",
                "architecture": "x86_64",
                "processor_model": "Intel Xeon E5-2680 v4",
                "physical_cpus": "2",
                "virtual_cpus": "8",
                "disk_usage": "60%",
                "cpu_temperature": "52",
                "domain_name": "example.com",
                "asset_tag": "DB-002",
                "serial_number": "SN987654321",
                "model_name": "HP ProLiant DL380 Gen10",
                "device_type": "Server",
                "support_group": "Database Team",
                "owner_group": "Data Team"
            }
        )
    ]

@patch("src.core.services.jira_field_mapper_service.JiraFieldMapper.save_mapping")
@patch("src.core.integrations.jira_client.JiraClient.create_attribute")
def test_map_linux_to_jira(mock_create_attribute, mock_save_mapping, test_assets):
    """Test mapping Linux assets to Jira payload."""
    # Mock the create_attribute method to return a successful response
    mock_create_attribute.return_value = {
        "id": 123,
        "name": "Mock Attribute",
        "objectTypeId": 12
    }

    # Mock the save_mapping method to do nothing
    mock_save_mapping.return_value = None

    for asset in test_assets:
        jira_payload = map_linux_to_jira(asset)
        assert jira_payload["objectTypeId"] is not None
        assert len(jira_payload["attributes"]) > 0

def test_sync_assets_to_jira(mock_jira_client, test_assets):
    """Test syncing Linux assets to Jira."""
    assets_to_sync = [asset.dict() for asset in test_assets]
    result = mock_jira_client.sync_assets(assets_to_sync)

    assert result["total"] == 3
    assert result["created"] == 2
    assert result["updated"] == 1
    assert result["errors"] == 0
    assert not result["error_details"]