#!/usr/bin/env python3
"""
Test script to generate Linux asset data and sync it to Jira.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.models.asset_model import LinuxAsset
from src.core.integrations.jira_client import JiraClient
from src.core.models.jira_model import map_linux_to_jira
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_linux_assets():
    """Create test Linux asset data."""
    
    test_assets = [
        LinuxAsset(
            name="web-server-01",
            type="linux",
            hostname="web-server-01",
            ip_address="192.168.1.100",
            os="Ubuntu 22.04 LTS",
            cpu_cores=8,  # Physical cores
            memory_mb=8192,  # 8 GB
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
            cpu_cores=16,  # Physical cores
            memory_mb=16384,  # 16 GB
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
        ),
        LinuxAsset(
            name="dev-workstation-03",
            type="linux",
            hostname="dev-workstation-03", 
            ip_address="192.168.1.102",
            os="CentOS Stream 9",
            cpu_cores=12,  # Physical cores
            memory_mb=12288,  # 12 GB
            kernel_version="5.14.0-362.18.1.el9_3.x86_64",
            distro="CentOS",
            package_count=1800,
            metadata={
                "discovery_method": "test_data",
                "environment": "development",
                "purpose": "development workstation",
                "last_updated": "2024-01-15T10:40:00Z",
                "memory_gb": "12",
                "architecture": "x86_64",
                "processor_model": "AMD Ryzen 5 5600X",
                "physical_cpus": "1",
                "virtual_cpus": "6",
                "disk_usage": "45%",
                "cpu_temperature": "38",
                "domain_name": "dev.example.com",
                "asset_tag": "DEV-003",
                "serial_number": "SN456789123",
                "model_name": "Custom Build",
                "device_type": "Workstation",
                "support_group": "Development Team",
                "owner_group": "Dev Team"
            }
        )
    ]
    
    return test_assets

def test_jira_mapping():
    """Test the Jira mapping functions."""
    logger.info("Testing Jira mapping functions...")
    
    test_assets = create_test_linux_assets()
    
    for asset in test_assets:
        logger.info(f"\n=== Testing mapping for {asset.hostname} ===")
        
        # Test the mapping function
        jira_payload = map_linux_to_jira(asset)
        
        logger.info(f"Object Type ID: {jira_payload['objectTypeId']}")
        logger.info(f"Number of attributes: {len(jira_payload['attributes'])}")
        
        # Show the mapped attributes
        for attr in jira_payload['attributes']:
            attr_id = attr['objectTypeAttributeId']
            attr_value = attr['objectAttributeValues'][0]['value']
            logger.info(f"  Attribute ID {attr_id}: {attr_value}")
    
    return test_assets

def test_jira_sync():
    """Test syncing assets to Jira."""
    logger.info("\n=== Testing Jira Sync ===")
    
    try:
        # Create test assets
        test_assets = create_test_linux_assets()
        
        # Convert to dict format (as expected by sync_assets)
        assets_to_sync = [asset.dict() for asset in test_assets]
        
        logger.info(f"Created {len(assets_to_sync)} test Linux assets")
        
        # Initialize Jira client
        jira_client = JiraClient()
        
        # Sync assets to Jira
        logger.info("Starting sync to Jira...")
        sync_results = jira_client.sync_assets(assets_to_sync)
        
        logger.info("Sync completed!")
        logger.info(f"Results: {sync_results}")
        
        return sync_results
        
    except Exception as e:
        logger.error(f"Sync test failed: {e}", exc_info=True)
        return None

def main():
    """Main test function."""
    logger.info("Starting Linux asset sync test...")
    
    # Test 1: Test mapping functions
    test_assets = test_jira_mapping()
    
    # Test 2: Test actual Jira sync
    sync_results = test_jira_sync()
    
    if sync_results:
        logger.info("\n=== Test Results Summary ===")
        logger.info(f"Total assets processed: {sync_results['total']}")
        logger.info(f"Created: {sync_results['created']}")
        logger.info(f"Updated: {sync_results['updated']}")
        logger.info(f"Errors: {sync_results['errors']}")
        
        if sync_results['error_details']:
            logger.error("Error details:")
            for error in sync_results['error_details']:
                logger.error(f"  - {error}")
    else:
        logger.error("Sync test failed!")

if __name__ == "__main__":
    main()
