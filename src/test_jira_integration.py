#!/usr/bin/env python3
"""
Test script for Jira integration.
This script tests the Jira client and service functionality.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.integrations.jira_client import JiraClient, JiraConfig
from core.services.jira_service import JiraService
from core.models.asset_model import LinuxAsset

def test_jira_config():
    """Test Jira configuration loading."""
    print("🔧 Testing Jira Configuration...")
    
    try:
        # Test with environment variables
        client = JiraClient()
        print(f"✅ Jira client initialized successfully")
        print(f"   Cloud ID: {client.config.cloud_id}")
        print(f"   Workspace ID: {client.config.workspace_id}")
        return True
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("   Make sure to set these environment variables:")
        print("   - JIRA_URL")
        print("   - JIRA_API_USER")
        print("   - JIRA_API_TOKEN")
        print("   - JIRA_WORKSPACE_ID")
        print("   - JIRA_CLOUD_ID")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_jira_client():
    """Test Jira client functionality."""
    print("\n🔧 Testing Jira Client...")
    
    try:
        client = JiraClient()
        
        # Test getting asset schemas
        print("   📋 Getting asset schemas...")
        schemas = client.get_asset_schemas()
        print(f"   ✅ Retrieved {len(schemas)} asset schemas")
        
        # Test querying assets
        print("   🔍 Querying assets...")
        assets = client.query_assets("ObjectType = \"Servers\"", results_per_page=10)
        print(f"   ✅ Retrieved {len(assets)} assets")
        
        if assets:
            print(f"   📦 Sample asset: {assets[0].label}")
        
        return True
        
    except Exception as e:
        print(f"❌ Jira client test failed: {e}")
        return False

def test_jira_service():
    """Test Jira service functionality."""
    print("\n🔧 Testing Jira Service...")
    
    try:
        service = JiraService()
        
        # Test getting all assets
        print("   📋 Getting all assets...")
        assets = service.get_all_assets()
        print(f"   ✅ Retrieved {len(assets)} assets")
        
        # Test getting asset schemas
        print("   📋 Getting asset schemas...")
        schemas = service.get_asset_schemas()
        print(f"   ✅ Retrieved {len(schemas)} asset schemas")
        
        return True
        
    except Exception as e:
        print(f"❌ Jira service test failed: {e}")
        return False

def test_asset_creation():
    """Test creating an asset from a model."""
    print("\n🔧 Testing Asset Creation...")
    
    try:
        service = JiraService()
        
        # Create a test Linux asset
        test_asset = LinuxAsset(
            name="test-server-01",
            hostname="test-server-01.local",
            ip_address="192.168.1.100",
            os="Ubuntu",
            cpu_cores=4,
            memory_mb=8192,
            distro="Ubuntu",
            kernel_version="5.15.0-52-generic",
            package_count=1500,
            metadata={"source": "test"}
        )
        
        print(f"   📦 Created test asset: {test_asset.hostname}")
        print(f"   🐧 OS: {test_asset.distro} {test_asset.kernel_version}")
        print(f"   💻 CPU: {test_asset.cpu_cores} cores, Memory: {test_asset.memory_mb} MB")
        
        # Note: We're not actually creating it in Jira to avoid test data
        print("   ⚠️  Skipping actual Jira creation (test mode)")
        
        return True
        
    except Exception as e:
        print(f"❌ Asset creation test failed: {e}")
        return False

def test_environment():
    """Test environment setup."""
    print("🔧 Testing Environment...")
    
    # Check required environment variables
    required_vars = [
        "JIRA_URL",
        "JIRA_API_USER", 
        "JIRA_API_TOKEN",
        "JIRA_WORKSPACE_ID",
        "JIRA_CLOUD_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("\nSet these variables in your .env file or environment:")
        for var in missing_vars:
            print(f"   export {var}=your_value")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main test function."""
    print("🚀 Jira Integration Test Suite")
    print("=" * 50)
    
    # Test environment first
    if not test_environment():
        print("\n❌ Environment test failed. Please set up your environment variables.")
        sys.exit(1)
    
    # Test configuration
    if not test_jira_config():
        print("\n❌ Configuration test failed. Please check your Jira settings.")
        sys.exit(1)
    
    # Test Jira client
    if not test_jira_client():
        print("\n❌ Jira client test failed. Please check your Jira API access.")
        sys.exit(1)
    
    # Test Jira service
    if not test_jira_service():
        print("\n❌ Jira service test failed. Please check your Jira service.")
        sys.exit(1)
    
    # Test asset creation
    if not test_asset_creation():
        print("\n❌ Asset creation test failed. Please check your asset models.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🏁 All tests passed! Jira integration is working correctly.")
    print("\nNext steps:")
    print("1. Test the API endpoints: /assets, /jira/assets")
    print("2. Try creating assets through the API")
    print("3. Test the discovery workflow")

if __name__ == "__main__":
    main()

