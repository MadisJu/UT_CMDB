# JIRAga seotud toimingud

from typing import List, Dict, Any, Optional
from src.core.integrations.jira_client import JiraClient
from src.api.schemas.jira import JiraAsset
from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.core.models.jira_model import map_host_to_jira, map_linux_to_jira, map_windows_to_jira, map_sparc_to_jira
import logging

logger = logging.getLogger(__name__)


class JiraService:
    
    def __init__(self, jira_client: Optional[JiraClient] = None):
        
        self.jira_client = jira_client or JiraClient()
    
    def get_all_assets(self, aql_query: str = "ObjectType = \"Servers\"") -> List[JiraAsset]:
        
        try:
            return self.jira_client.query_assets(aql_query)
        except Exception as e:
            logger.error(f"Failed to get assets from Jira: {e}")
            raise
    
    def get_asset_schemas(self) -> Dict[str, Any]:
        
        try:
            return self.jira_client.get_asset_schemas()
        except Exception as e:
            logger.error(f"Failed to get asset schemas from Jira: {e}")
            raise
    
    def create_asset_from_model(self, asset: HostAsset) -> JiraAsset:

        try:
            if isinstance(asset, LinuxAsset):
                jira_data = map_linux_to_jira(asset)
            elif isinstance(asset, WindowsAsset):
                jira_data = map_windows_to_jira(asset)
            elif isinstance(asset, SparcAsset):
                jira_data = map_sparc_to_jira(asset)
            else:
                jira_data = map_host_to_jira(asset)
            
            jira_data["label"] = asset.hostname or asset.name
            
            logger.info(f"Creating asset in Jira: {asset.hostname}")
            logger.info(f"Jira data: {jira_data}")
            return self.jira_client.create_asset(jira_data)
            
        except Exception as e:
            logger.error(f"Failed to create asset in Jira: {e}")
            raise
    
    def update_asset_from_model(self, asset_id: str, asset: HostAsset) -> JiraAsset:

        try:
            if isinstance(asset, LinuxAsset):
                jira_data = map_linux_to_jira(asset)
            elif isinstance(asset, WindowsAsset):
                jira_data = map_windows_to_jira(asset)
            elif isinstance(asset, SparcAsset):
                jira_data = map_sparc_to_jira(asset)
            else:
                jira_data = map_host_to_jira(asset)
            
            jira_data["label"] = asset.hostname or asset.name
            
            logger.info(f"Updating asset in Jira: {asset_id}")
            return self.jira_client.update_asset(asset_id, jira_data)
            
        except Exception as e:
            logger.error(f"Failed to update asset in Jira: {e}")
            raise
    
    def sync_assets_from_models(self, assets: List[HostAsset]) -> Dict[str, Any]:

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

        try:
            aql_query = f'ObjectType = "Servers" AND Hostname = "{hostname}"'
            assets = self.jira_client.query_assets(aql_query)
            
            if assets:
                return assets[0] 
            return None
            
        except Exception as e:
            logger.error(f"Failed to find asset by hostname: {e}")
            return None
    
    def delete_asset(self, asset_id: str) -> bool:

        try:
            logger.info(f"Deleting asset from Jira: {asset_id}")
            return self.jira_client.delete_asset(asset_id)
        except Exception as e:
            logger.error(f"Failed to delete asset from Jira: {e}")
            raise
    
    def get_asset_by_id(self, asset_id: str) -> JiraAsset:

        try:
            return self.jira_client.get_asset_by_id(asset_id)
        except Exception as e:
            logger.error(f"Failed to get asset by ID: {e}")
            raise
