import os
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from src.api.schemas.jira import JiraAsset, JiraAssetAttribute, JiraAQLResponse

logger = logging.getLogger(__name__)


class JiraConfig(BaseModel):
    """Jira configuration model."""
    url: str
    user: str
    token: str
    workspace_id: str
    cloud_id: str


class JiraClient:
    """Jira Asset Management client for CMDB operations."""
    
    def __init__(self, config: Optional[JiraConfig] = None):
        """
        Initialize Jira client.
        
        Args:
            config: Jira configuration. If None, loads from environment variables.
        """
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.base_url = f"https://api.atlassian.com/ex/jira/{config.cloud_id}/jsm/assets/workspace/{config.workspace_id}/v1"
        
    def _load_config_from_env(self) -> JiraConfig:
        """Load Jira configuration from environment variables."""
        try:
            from src.core.configs.config import settings
            if settings.jira_url and settings.jira_user_email and settings.jira_api_token:
                return JiraConfig(
                    url=settings.jira_url,
                    user=settings.jira_user_email,
                    token=settings.jira_api_token,
                    workspace_id=settings.jira_asset_workspace_id,
                    cloud_id=settings.jira_cloud_id
                )
        except Exception as e:
            logger.warning(f"Failed to load Jira config from Settings: {e}")
        
        config_vars = {
            "url": os.getenv("JIRA_URL"),
            "user": os.getenv("JIRA_API_USER"),
            "token": os.getenv("JIRA_API_TOKEN"),
            "workspace_id": os.getenv("JIRA_WORKSPACE_ID"),
            "cloud_id": os.getenv("JIRA_CLOUD_ID")
        }
        
        if not all(config_vars.values()):
            missing_vars = [k for k, v in config_vars.items() if not v]
            raise ValueError(f"Missing Jira configuration variables: {missing_vars}")
        
        return JiraConfig(
            url=config_vars["url"],
            user=config_vars["user"],
            token=config_vars["token"],
            workspace_id=config_vars["workspace_id"],
            cloud_id=config_vars["cloud_id"]
        )
    
    def _get_auth(self) -> tuple:
        """Get authentication tuple for requests."""
        return (self.config.user, self.config.token)
    
    def _get_headers(self) -> dict:
        """Get standard headers for requests."""
        return {"Accept": "application/json", "Content-Type": "application/json"}
    
    def query_assets(self, aql_query: str = "ObjectType = \"Servers\"", results_per_page: int = 50) -> List[JiraAsset]:
        """
        Query assets from Jira using AQL.
        
        Args:
            aql_query: AQL query string
            results_per_page: Number of results per page
            
        Returns:
            List of Jira assets
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/aql/objects"
        headers = self._get_headers()
        auth = self._get_auth()
        params = {"qlQuery": aql_query, "resultsPerPage": results_per_page}
        
        try:
            logger.info(f"Querying Jira assets with AQL: {aql_query}")
            response = requests.get(endpoint, headers=headers, params=params, auth=auth)
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
        
        Returns:
            Dictionary containing asset schemas
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        endpoint = f"{self.base_url}/objectschema/list"
        headers = self._get_headers()
        auth = self._get_auth()
        
        try:
            logger.info("Fetching Jira asset schemas")
            response = requests.get(endpoint, headers=headers, auth=auth)
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
        endpoint = f"{self.base_url}/objects"
        headers = self._get_headers()
        auth = self._get_auth()
        
        try:
            logger.info(f"Creating asset in Jira: {asset_data.get('label', 'Unknown')}")
            response = requests.post(endpoint, headers=headers, json=asset_data, auth=auth)
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
        endpoint = f"{self.base_url}/objects/{asset_id}"
        headers = self._get_headers()
        auth = self._get_auth()
        
        try:
            logger.info(f"Updating asset in Jira: {asset_id}")
            response = requests.put(endpoint, headers=headers, json=asset_data, auth=auth)
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
        endpoint = f"{self.base_url}/objects/{asset_id}"
        headers = self._get_headers()
        auth = self._get_auth()
        
        try:
            logger.info(f"Deleting asset from Jira: {asset_id}")
            response = requests.delete(endpoint, headers=headers, auth=auth)
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
        endpoint = f"{self.base_url}/objects/{asset_id}"
        headers = self._get_headers()
        auth = self._get_auth()
        
        try:
            logger.info(f"Retrieving asset from Jira: {asset_id}")
            response = requests.get(endpoint, headers=headers, auth=auth)
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
    
    def sync_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sync multiple assets to Jira.
        
        Args:
            assets: List of assets to sync
            
        Returns:
            Sync results summary
            
        Raises:
            requests.exceptions.HTTPError: If API request fails
        """
        results = {
            "total": len(assets),
            "created": 0,
            "updated": 0,
            "errors": 0,
            "error_details": []
        }
        
        for asset in assets:
            try:
                created_asset = self.create_asset(asset)
                results["created"] += 1
                logger.info(f"Created asset: {created_asset.objectKey}")
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:
                    try:
                        logger.warning(f"Asset might already exist, skipping: {asset.get('label', 'Unknown')}")
                        results["errors"] += 1
                        results["error_details"].append(f"Asset already exists: {asset.get('label', 'Unknown')}")
                    except Exception as update_error:
                        results["errors"] += 1
                        results["error_details"].append(f"Update failed: {str(update_error)}")
                else:
                    results["errors"] += 1
                    results["error_details"].append(f"Creation failed: {e.response.text}")
                    logger.error(f"Failed to create asset: {e.response.text}")
            except Exception as e:
                results["errors"] += 1
                results["error_details"].append(f"Unexpected error: {str(e)}")
                logger.error(f"Unexpected error syncing asset: {e}")
        
        logger.info(f"Sync completed: {results['created']} created, {results['updated']} updated, {results['errors']} errors")
        return results
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make a request with proper authentication and headers.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        headers = kwargs.pop('headers', {})
        headers.update(self._get_headers())
        
        auth = kwargs.pop('auth', self._get_auth())
        
        return requests.request(method, url, headers=headers, auth=auth, **kwargs)
    
    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Jira issue (fallback method when Asset Management fails).
        
        Args:
            issue_data: The issue data to create
            
        Returns:
            Created issue response
        """
        try:
            unique_id = self.config.cloud_id
            url = f"https://api.atlassian.com/ex/jira/{unique_id}/rest/api/3/issue"
            
            response = self._make_request("POST", url, json=issue_data)
            
            if response.status_code in [200, 201]:
                issue = response.json()
                logger.info(f"Successfully created Jira issue: {issue.get('key')}")
                return issue
            else:
                logger.error(f"Failed to create Jira issue: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create issue: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            raise
