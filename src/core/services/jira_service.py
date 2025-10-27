"""
Jira service for CMDB operations.
This service handles all Jira-related operations and integrates with the asset models.
"""

from typing import List, Dict, Any, Optional
from src.core.integrations.jira_client import JiraClient
from src.api.schemas.jira import JiraAsset
from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.core.models.jira_model import map_host_to_jira, map_linux_to_jira, map_windows_to_jira, map_sparc_to_jira
import logging

logger = logging.getLogger(__name__)


class JiraService:
    """Service for Jira Asset Management operations."""
    
    def __init__(self, jira_client: Optional[JiraClient] = None):
        """
        Initialize Jira service.
        
        Args:
            jira_client: Jira client instance. If None, creates a new one.
        """
        self.jira_client = jira_client or JiraClient()
    
    def get_all_assets(self, aql_query: str = "ObjectType = \"Servers\"") -> List[JiraAsset]:
        """
        Get all assets from Jira.
        
        Args:
            aql_query: AQL query to filter assets
            
        Returns:
            List of Jira assets
        """
        try:
            return self.jira_client.query_assets(aql_query)
        except Exception as e:
            logger.error(f"Failed to get assets from Jira: {e}")
            raise
    
    def get_asset_schemas(self) -> Dict[str, Any]:
        """
        Get asset schemas from Jira.
        
        Returns:
            Asset schemas dictionary
        """
        try:
            return self.jira_client.get_asset_schemas()
        except Exception as e:
            logger.error(f"Failed to get asset schemas from Jira: {e}")
            raise
    
    def create_asset_from_model(self, asset: HostAsset) -> JiraAsset:
        """
        Create a Jira asset from an asset model.
        
        Args:
            asset: Asset model to create in Jira
            
        Returns:
            Created Jira asset
        """
        try:
            # Determine the appropriate mapping function based on asset type
            if isinstance(asset, LinuxAsset):
                jira_data = map_linux_to_jira(asset)
            elif isinstance(asset, WindowsAsset):
                jira_data = map_windows_to_jira(asset)
            elif isinstance(asset, SparcAsset):
                jira_data = map_sparc_to_jira(asset)
            else:
                jira_data = map_host_to_jira(asset)
            
            # Add label for the asset
            jira_data["label"] = asset.hostname or asset.name
            
            logger.info(f"Creating asset in Jira: {asset.hostname}")
            return self.jira_client.create_asset(jira_data)
            
        except Exception as e:
            logger.error(f"Failed to create asset in Jira: {e}")
            raise
    
    def update_asset_from_model(self, asset_id: str, asset: HostAsset) -> JiraAsset:
        """
        Update a Jira asset from an asset model.
        
        Args:
            asset_id: ID of the asset to update
            asset: Asset model with updated data
            
        Returns:
            Updated Jira asset
        """
        try:
            # Determine the appropriate mapping function based on asset type
            if isinstance(asset, LinuxAsset):
                jira_data = map_linux_to_jira(asset)
            elif isinstance(asset, WindowsAsset):
                jira_data = map_windows_to_jira(asset)
            elif isinstance(asset, SparcAsset):
                jira_data = map_sparc_to_jira(asset)
            else:
                jira_data = map_host_to_jira(asset)
            
            # Add label for the asset
            jira_data["label"] = asset.hostname or asset.name
            
            logger.info(f"Updating asset in Jira: {asset_id}")
            return self.jira_client.update_asset(asset_id, jira_data)
            
        except Exception as e:
            logger.error(f"Failed to update asset in Jira: {e}")
            raise
    
    def sync_assets_from_models(self, assets: List[HostAsset]) -> Dict[str, Any]:
        """
        Sync multiple asset models to Jira.
        
        Args:
            assets: List of asset models to sync
            
        Returns:
            Sync results summary
        """
        try:
            jira_assets = []
            for asset in assets:
                if isinstance(asset, LinuxAsset):
                    jira_data = map_linux_to_jira(asset)
                elif isinstance(asset, WindowsAsset):
                    jira_data = map_windows_to_jira(asset)
                elif isinstance(asset, SparcAsset):
                    jira_data = map_sparc_to_jira(asset)
                else:
                    jira_data = map_host_to_jira(asset)
                
                jira_data["label"] = asset.hostname or asset.name
                jira_assets.append(jira_data)
            
            logger.info(f"Syncing {len(assets)} assets to Jira")
            return self.jira_client.sync_assets(jira_assets)
            
        except Exception as e:
            logger.error(f"Failed to sync assets to Jira: {e}")
            raise
    
    def find_asset_by_hostname(self, hostname: str) -> Optional[JiraAsset]:
        """
        Find an asset by hostname.
        
        Args:
            hostname: Hostname to search for
            
        Returns:
            Jira asset if found, None otherwise
        """
        try:
            # Query for assets with the specific hostname
            aql_query = f'ObjectType = "Servers" AND Hostname = "{hostname}"'
            assets = self.jira_client.query_assets(aql_query)
            
            if assets:
                return assets[0]  # Return first match
            return None
            
        except Exception as e:
            logger.error(f"Failed to find asset by hostname: {e}")
            return None
    
    def delete_asset(self, asset_id: str) -> bool:
        """
        Delete an asset from Jira.
        
        Args:
            asset_id: ID of the asset to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            logger.info(f"Deleting asset from Jira: {asset_id}")
            return self.jira_client.delete_asset(asset_id)
        except Exception as e:
            logger.error(f"Failed to delete asset from Jira: {e}")
            raise
    
    def get_asset_by_id(self, asset_id: str) -> JiraAsset:
        """
        Get an asset by ID.
        
        Args:
            asset_id: ID of the asset to retrieve
            
        Returns:
            Jira asset
        """
        try:
            return self.jira_client.get_asset_by_id(asset_id)
        except Exception as e:
            logger.error(f"Failed to get asset by ID: {e}")
            raise
