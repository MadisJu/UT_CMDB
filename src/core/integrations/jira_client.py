import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from src.api.schemas.jira import JiraAsset, JiraAssetAttribute, JiraAQLResponse
from src.core.configs.config import Settings
from src.core.models.fact_parser import parse_facts_to_asset
from src.core.models.asset_model import HostAsset 

logger = logging.getLogger(__name__)


class JiraClient:
    """Jira Asset Management client for CMDB operations."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Jira client.
        
        Args:
            settings: Application settings object. If None, loads from global settings.
        """
        if settings is None:
            from src.core.configs.config import settings as global_settings
            settings = global_settings
            
        self.email = settings.jira_user_email
        self.token = settings.jira_api_token
        self.cloud_id = settings.jira_cloud_id
        self.workspace_id = settings.jira_asset_workspace_id
        
        if not all([self.email, self.token, self.cloud_id, self.workspace_id]):
            raise ValueError("Jira credentials, cloud ID, and workspace ID must be set in settings.")

        self.base_url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/jsm/assets/workspace/{self.workspace_id}/v1"
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def query_assets(self, aql_query: str = "ObjectType = \"Servers\"", results_per_page: int = 50) -> List[JiraAsset]:
        """
        Query assets from Jira using AQL.
        (See oli õige, seda ei muuda)
        """
        endpoint = f"{self.base_url}/aql/objects"
        params = {"qlQuery": aql_query, "resultsPerPage": results_per_page}
        
        try:
            logger.info(f"Querying Jira assets with AQL: {aql_query}")
            response = requests.get(endpoint, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            
            data = JiraAQLResponse(**response.json())
            logger.info(f"Retrieved {len(data.objectEntries)} assets from Jira")
            return data.objectEntries
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API query failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error querying Jira assets: {e}")
            raise
    
    def get_asset_schemas(self) -> Dict[str, Any]:
        """
        Get all asset schemas from Jira.
        (See oli õige, seda ei muuda)
        """
        endpoint = f"{self.base_url}/objectschema/list"
        
        try:
            logger.info("Fetching Jira asset schemas")
            response = requests.get(endpoint, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            schemas = response.json()
            logger.info(f"Retrieved {len(schemas)} asset schemas from Jira")
            return schemas
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API schema request failed: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Jira API connection failed: {e}")
            raise
    
    def create_asset(self, asset_data: Dict[str, Any]) -> JiraAsset:
        """
        Create a new asset in Jira.
        
        Args:
            asset_data: Asset data in Jira format
            
        Returns:
            Created Jira asset
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/object/create" # <--- PARANDATUD
        
        try:
            logger.info(f"Creating asset in Jira: {asset_data.get('label', 'Unknown')}")
            response = requests.post(endpoint, headers=self.headers, json=asset_data, auth=self.auth)
            response.raise_for_status()
            
            created_asset = JiraAsset(**response.json())
            logger.info(f"Successfully created asset: {created_asset.objectKey}")
            return created_asset
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API asset creation failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating asset: {e}")
            raise
    
    def update_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> JiraAsset:
        """
        Update an existing asset in Jira.
        
        Args:
            asset_id: ID of the asset to update
            asset_data: Updated asset data in Jira format
            
        Returns:
            Updated Jira asset
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/object/{asset_id}"  # <--- PARANDATUD
        
        try:
            logger.info(f"Updating asset in Jira: {asset_id}")
            response = requests.put(endpoint, headers=self.headers, json=asset_data, auth=self.auth)
            response.raise_for_status()
            
            updated_asset = JiraAsset(**response.json())
            logger.info(f"Successfully updated asset: {updated_asset.objectKey}")
            return updated_asset
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API asset update failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating asset: {e}")
            raise
    
    def delete_asset(self, asset_id: str) -> bool:
        """
        Delete an asset from Jira.
        
        Args:
            asset_id: ID of the asset to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
    
        endpoint = f"{self.base_url}/object/{asset_id}"  # <--- PARANDATUD
        
        try:
            logger.info(f"Deleting asset from Jira: {asset_id}")
            response = requests.delete(endpoint, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            logger.info(f"Successfully deleted asset: {asset_id}")
            return True
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API asset deletion failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting asset: {e}")
            raise
    
    def get_asset_by_id(self, asset_id: str) -> JiraAsset:
        """
        Get a specific asset by ID.
        
        Args:
            asset_id: ID of the asset to retrieve
            
        Returns:
            Jira asset
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/object/{asset_id}"  # <--- PARANDATUD
        
        try:
            logger.info(f"Retrieving asset from Jira: {asset_id}")
            response = requests.get(endpoint, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            asset = JiraAsset(**response.json())
            logger.info(f"Successfully retrieved asset: {asset.objectKey}")
            return asset
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API asset retrieval failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving asset: {e}")
            raise


    def find_asset_by_hostname(self, hostname: str) -> Optional[str]:
        """
        Find a Jira asset by its hostname.
        
        Args:
            hostname: The hostname to search for.
            
        Returns:
            The asset ID if found, otherwise None.
        """
        # The 'Name' attribute in Jira is used to store the hostname.
        aql_query = f'Name = "{hostname}"'
        try:
            logger.info(f"Searching for asset with hostname: {hostname}")
            assets = self.query_assets(aql_query)
            if assets:
                asset_id = assets[0].id
                logger.info(f"Found existing asset with ID: {asset_id}")
                return asset_id
            else:
                logger.info(f"No existing asset found for hostname: {hostname}")
                return None
        except Exception as e:
            logger.error(f"Error finding asset by hostname '{hostname}': {e}")
            return None    
    
    def sync_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync a list of assets to Jira, creating or updating them.
        """
        logger.info(f"Syncing {len(assets)} assets to Jira")
        results = {"total": len(assets), "created": 0, "updated": 0, "errors": 0, "error_details": []}

        for asset_data in assets:
            # The asset_data is already a dictionary from the HostAsset model.
            # We can directly create the HostAsset instance from it.
            try:
                asset_model = HostAsset(**asset_data)
                hostname = asset_model.hostname
                
                logger.info(f"Preparing to create/update asset in Jira for: {hostname}")
                
                existing_asset_id = self.find_asset_by_hostname(hostname)
                jira_payload = self._prepare_jira_payload(asset_model)

                if existing_asset_id:
                    logger.info(f"Updating asset in Jira: {hostname} (ID: {existing_asset_id})")
                    self.update_asset(existing_asset_id, jira_payload)
                    results["updated"] += 1
                    logger.info(f"Successfully updated asset for hostname {hostname}")
                else:
                    logger.info(f"Creating asset in Jira: {hostname.capitalize()}")
                    created_asset = self.create_asset(jira_payload)
                    results["created"] += 1
                    # The response from create_asset is a JiraAsset model, which has .objectKey
                    asset_key = created_asset.objectKey if created_asset else 'N/A'
                    logger.info(f"Successfully created asset {asset_key} for hostname {hostname}")

            except Exception as e:
                # Use the hostname from the model if available, otherwise fallback
                hostname_for_error = asset_data.get("hostname", "unknown")
                logger.error(f"Sync failed for {hostname_for_error}: {e}", exc_info=True)
                results["errors"] += 1
                results["error_details"].append(f"Sync failed for {hostname_for_error}: {e}")
        
        logger.info(f"Sync completed: {results['created']} created, {results['updated']} updated, {results['errors']} errors")
        return results
    

    def _prepare_jira_payload(self, asset: HostAsset) -> Dict[str, Any]:
        """
        Prepare the JSON payload for creating/updating a Jira asset.
        
        Args:
            asset: The HostAsset object.
            
        Returns:
            A dictionary formatted for the Jira API.
        """
        # This maps your HostAsset fields to the IDs of your Jira Asset custom fields.
        # You MUST replace these placeholder IDs with the real IDs from your Jira instance.
        # To find these IDs, go to your Jira Assets schema configuration.
        
        # --- Placeholder IDs ---
        name_field_id = "150"
        hostname_field_id = "178" 
        ip_address_field_id = "177"
        cpu_model = "174"
        cpu_cores_field_id = "181"
        memory_field_id = "175"
        # -----------------------

        attributes = [
            {"objectTypeAttributeId": name_field_id, "objectAttributeValues": [{"value": asset.hostname}]},
            {"objectTypeAttributeId": hostname_field_id, "objectAttributeValues": [{"value": asset.hostname}]},
            {"objectTypeAttributeId": ip_address_field_id, "objectAttributeValues": [{"value": asset.ip_address}]},
            {"objectTypeAttributeId": cpu_model, "objectAttributeValues": [{"value": asset.os}]},
            {"objectTypeAttributeId": cpu_cores_field_id, "objectAttributeValues": [{"value": str(asset.cpu_cores)}]},
            {"objectTypeAttributeId": memory_field_id, "objectAttributeValues": [{"value": str(asset.memory_mb)}]},
        ]
        
        # The objectTypeId for "Servers" or a similar object type in your Jira schema.
        # You MUST replace this placeholder ID.
        server_object_type_id = "25" 

        return {
            "objectTypeId": server_object_type_id,
            "attributes": attributes
        }