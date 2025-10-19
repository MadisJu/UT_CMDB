import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.services.jira_service import JiraService
from src.core.integrations.jira_client import JiraClient
from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.core.models.fact_parser import parse_facts_to_asset

logger = logging.getLogger(__name__)

# Task for syncing data to JIRA

@celery_app.task(name="src.worker.tasks.sync_to_jira.sync_task", max_retries=3, bind=True)
def sync_task(self, payload):
    """
    Celery task for syncing assets to Jira.
    
    Args:
        payload: List of asset dictionaries to sync
        
    Returns:
        Dictionary containing sync results
    """
    try:
        logger.info(f"Starting sync task for {len(payload)} assets")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(payload), 'status': 'Initializing Jira sync...'}
        )
        
        # Initialize Jira service
        jira_client = JiraClient()
        jira_service = JiraService(jira_client)
        
        # Convert payload to asset models
        assets = []
        for i, asset_data in enumerate(payload):
            try:
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(payload), 
                        'status': f'Processing asset {i+1}/{len(payload)}'
                    }
                )
                
                # Create appropriate asset model based on type
                if asset_data.get("type") == "linux":
                    asset = LinuxAsset(**asset_data)
                elif asset_data.get("type") == "windows":
                    asset = WindowsAsset(**asset_data)
                elif asset_data.get("type") == "sparc":
                    asset = SparcAsset(**asset_data)
                else:
                    asset = HostAsset(**asset_data)
                
                assets.append(asset)
                
            except Exception as e:
                logger.error(f"Failed to create asset model for item {i}: {e}")
                # Create fallback asset
                fallback_asset = HostAsset(
                    name=asset_data.get("name", f"unknown_{i}"),
                    hostname=asset_data.get("hostname", f"unknown_{i}"),
                    ip_address=asset_data.get("ip_address", "unknown"),
                    os="Unknown",
                    metadata={"source": "sync_fallback", "error": str(e)}
                )
                assets.append(fallback_asset)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': len(assets), 'total': len(payload), 'status': 'Syncing assets to Jira...'}
        )
        
        # Sync assets to Jira
        sync_results = jira_service.sync_assets_from_models(assets)
        
        logger.info(f"Successfully synced {len(assets)} assets to Jira")
        
        # Return results
        return {
            "status": "success",
            "synced_items": len(assets),
            "sync_results": sync_results,
            "total_processed": len(payload)
        }
    
    except Exception as exc:
        logger.error(f"Sync task failed: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': len(payload), 'status': f'Sync failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="src.worker.tasks.sync_to_jira.sync_discovered_assets", max_retries=3, bind=True)
def sync_discovered_assets(self, discovery_result):
    """
    Celery task for syncing discovered assets to Jira.
    
    Args:
        discovery_result: Result from discovery task containing assets
        
    Returns:
        Dictionary containing sync results
    """
    try:
        logger.info("Starting sync of discovered assets to Jira")
        
        # Extract assets from discovery result
        if isinstance(discovery_result, dict) and "assets" in discovery_result:
            assets_data = discovery_result["assets"]
        elif isinstance(discovery_result, list):
            assets_data = discovery_result
        else:
            # Single asset
            assets_data = [discovery_result]
        
        logger.info(f"Syncing {len(assets_data)} discovered assets")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(assets_data), 'status': 'Initializing sync of discovered assets...'}
        )
        
        # Initialize Jira service
        jira_client = JiraClient()
        jira_service = JiraService(jira_client)
        
        # Convert to asset models
        assets = []
        for i, asset_data in enumerate(assets_data):
            try:
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(assets_data), 
                        'status': f'Processing discovered asset {i+1}/{len(assets_data)}'
                    }
                )
                
                # Create asset model
                if isinstance(asset_data, dict):
                    # Determine asset type from the data
                    if asset_data.get("type") == "linux" or "distro" in asset_data:
                        asset = LinuxAsset(**asset_data)
                    elif asset_data.get("type") == "windows" or "os_version" in asset_data:
                        asset = WindowsAsset(**asset_data)
                    elif asset_data.get("type") == "sparc" or "solaris_version" in asset_data:
                        asset = SparcAsset(**asset_data)
                    else:
                        asset = HostAsset(**asset_data)
                else:
                    # Assume it's already an asset model
                    asset = asset_data
                
                assets.append(asset)
                
            except Exception as e:
                logger.error(f"Failed to process discovered asset {i}: {e}")
                # Create fallback asset
                fallback_asset = HostAsset(
                    name=f"discovered_{i}",
                    hostname=f"discovered_{i}",
                    ip_address="unknown",
                    os="Unknown",
                    metadata={"source": "discovery_sync_fallback", "error": str(e)}
                )
                assets.append(fallback_asset)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': len(assets), 'total': len(assets_data), 'status': 'Syncing discovered assets to Jira...'}
        )
        
        # Sync assets to Jira
        sync_results = jira_service.sync_assets_from_models(assets)
        
        logger.info(f"Successfully synced {len(assets)} discovered assets to Jira")
        
        # Return results
        return {
            "status": "success",
            "synced_items": len(assets),
            "sync_results": sync_results,
            "discovery_method": discovery_result.get("discovery_method", "unknown"),
            "total_discovered": len(assets_data)
        }
    
    except Exception as exc:
        logger.error(f"Sync of discovered assets failed: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': len(assets_data) if 'assets_data' in locals() else 1, 'status': f'Sync of discovered assets failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)