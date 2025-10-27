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
    
    def get_object_type_schema(self, object_type_id: str = "25") -> Dict[str, Any]:
        """
        Get the schema for a specific object type, including all attribute definitions.
        
        Args:
            object_type_id: The ID of the object type (default: "25" for Servers/Hardware)
            
        Returns:
            Object type schema with all attributes
        """
        # Use the working endpoint that we know works
        endpoint = f"{self.base_url}/objectschema/list"
        
        try:
            logger.info(f"Fetching all object schemas to find attributes for type ID: {object_type_id}")
            response = requests.get(endpoint, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            all_schemas = response.json()
            
            # Debug: print the structure
            print(f"Response type: {type(all_schemas)}")
            if isinstance(all_schemas, dict):
                print(f"Response keys: {list(all_schemas.keys())}")
            elif isinstance(all_schemas, list):
                print(f"Response length: {len(all_schemas)}")
                if len(all_schemas) > 0:
                    print(f"First item type: {type(all_schemas[0])}")
                    print(f"First item keys: {list(all_schemas[0].keys()) if isinstance(all_schemas[0], dict) else 'N/A'}")
            
            # Handle different response structures
            schemas_to_search = []
            if isinstance(all_schemas, dict):
                # Check for paginated response
                if 'values' in all_schemas:
                    schemas_to_search = all_schemas['values']
                # If it's a dict, it might contain schemas directly or in a nested structure
                elif 'objectTypes' in all_schemas:
                    schemas_to_search = [all_schemas]
                elif 'schemas' in all_schemas:
                    schemas_to_search = all_schemas['schemas']
                else:
                    # Try to find any nested structure that might contain objectTypes
                    for key, value in all_schemas.items():
                        if isinstance(value, dict) and 'objectTypes' in value:
                            schemas_to_search.append(value)
                        elif isinstance(value, list):
                            schemas_to_search.extend(value)
            elif isinstance(all_schemas, list):
                schemas_to_search = all_schemas
            
            # Find the object type in the schemas
            print(f"Searching in {len(schemas_to_search)} schemas...")
            for i, schema in enumerate(schemas_to_search):
                print(f"Schema {i}: ID={schema.get('id')}, Name={schema.get('name')}")
                
                # Each schema contains object types, we need to fetch them
                if isinstance(schema, dict) and 'id' in schema:
                    schema_id = schema['id']
                    try:
                        # Fetch object types for this schema
                        # Try different endpoints for object types
                        endpoints_to_try = [
                            f"{self.base_url}/objectschema/{schema_id}/objecttypes",
                            f"{self.base_url}/objectschema/{schema_id}/objecttype",
                            f"{self.base_url}/objecttype?schemaId={schema_id}",
                            f"{self.base_url}/objectschema/{schema_id}"
                        ]
                        
                        schema_data = None
                        for endpoint in endpoints_to_try:
                            try:
                                print(f"Trying endpoint: {endpoint}")
                                schema_response = requests.get(endpoint, headers=self.headers, auth=self.auth)
                                schema_response.raise_for_status()
                                schema_data = schema_response.json()
                                print(f"Success with endpoint: {endpoint}")
                                break
                            except Exception as e:
                                print(f"Failed with endpoint {endpoint}: {e}")
                                continue
                        
                        if not schema_data:
                            print(f"No working endpoint found for schema {schema_id}")
                            continue
                        
                        print(f"Schema {schema_id} response type: {type(schema_data)}")
                        if isinstance(schema_data, list):
                            print(f"Schema {schema_id} contains {len(schema_data)} object types")
                            object_types = schema_data
                        elif isinstance(schema_data, dict):
                            print(f"Schema {schema_id} response keys: {list(schema_data.keys())}")
                            # Try different possible keys for object types
                            object_types = []
                            for key in ['objectTypes', 'objectTypeDefinitions', 'types', 'definitions', 'values']:
                                if key in schema_data:
                                    object_types = schema_data[key]
                                    print(f"Found object types in key '{key}': {len(object_types)} types")
                                    break
                        else:
                            print(f"Unexpected response type: {type(schema_data)}")
                            continue
                        
                        for obj_type in object_types:
                            print(f"  Object type ID: {obj_type.get('id')}, Name: {obj_type.get('name')}")
                            if str(obj_type.get('id')) == str(object_type_id):
                                # Found the object type, now fetch its attributes
                                try:
                                    # Use the correct JSM Assets API endpoint for attributes
                                    # The /objecttype/{id}/attributes endpoint worked and returned a list
                                    attr_endpoints = [
                                        f"{self.base_url}/objecttype/{object_type_id}/attributes",
                                        f"{self.base_url}/objecttypeattribute?objectTypeId={object_type_id}",
                                        f"{self.base_url}/objecttypeattribute/{object_type_id}",
                                        f"{self.base_url}/objecttype/{object_type_id}/attribute",
                                        f"{self.base_url}/objecttype/{object_type_id}",
                                        f"{self.base_url}/objectschema/{schema_id}/objecttype/{object_type_id}/attributes"
                                    ]
                                    
                                    attr_data = None
                                    for endpoint in attr_endpoints:
                                        try:
                                            print(f"Trying attribute endpoint: {endpoint}")
                                            attr_response = requests.get(endpoint, headers=self.headers, auth=self.auth)
                                            attr_response.raise_for_status()
                                            attr_data = attr_response.json()
                                            print(f"Success with attribute endpoint: {endpoint}")
                                            print(f"Attribute response type: {type(attr_data)}")
                                            if isinstance(attr_data, dict):
                                                print(f"Attribute response keys: {list(attr_data.keys())}")
                                            elif isinstance(attr_data, list):
                                                print(f"Attribute response length: {len(attr_data)}")
                                            break
                                        except Exception as e:
                                            print(f"Failed with attribute endpoint {endpoint}: {e}")
                                            continue
                                    
                                    if attr_data:
                                        return attr_data
                                    else:
                                        print(f"No working attribute endpoint found for object type {object_type_id}")
                                        return obj_type
                                except Exception as e:
                                    print(f"Failed to fetch attributes for object type {object_type_id}: {e}")
                                    # Return the basic object type info if attribute fetch fails
                                    return obj_type
                    except Exception as e:
                        print(f"Failed to fetch schema {schema_id}: {e}")
                        continue
            
            raise ValueError(f"Object type {object_type_id} not found")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Jira API schema request failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving object type schema: {e}")
            raise
    
    def list_object_attributes(self, object_type_id: str = "25") -> None:
        """
        List all available attributes for an object type with their IDs.
        Useful for finding the correct attribute IDs to use in sync operations.
        
        Args:
            object_type_id: The ID of the object type (default: "25" for Servers/Hardware)
        """
        try:
            schema = self.get_object_type_schema(object_type_id)
            
            print(f"\n=== Attributes for Object Type {object_type_id} ===\n")
            
            # Handle different response types
            attributes = None
            if isinstance(schema, list):
                # Direct list of attributes
                attributes = schema
                print(f"Found {len(attributes)} attributes in direct list")
            elif isinstance(schema, dict):
                # Try different possible key names for attributes
                for key in ["objectTypeAttributes", "attributes", "attributeDefinitions", "typeAttributes"]:
                    if key in schema:
                        attributes = schema[key]
                        print(f"Found attributes in key '{key}': {len(attributes)} attributes")
                        break
            
            if attributes:
                print(f"\n=== {len(attributes)} Attributes Found ===\n")
                for attr in attributes:
                    attr_id = attr.get('id') or attr.get('attributeId') or attr.get('objectTypeAttributeId')
                    attr_name = attr.get('name') or attr.get('label') or attr.get('attributeName')
                    attr_type = attr.get('type') or attr.get('attributeType') or attr.get('dataType')
                    attr_description = attr.get('description', '')
                    print(f"Name: {attr_name:<30} ID: {attr_id:<10} Type: {attr_type}")
                    if attr_description:
                        print(f"  Description: {attr_description}")
            else:
                print("No attributes found in schema response")
                print(f"\nSchema structure:")
                if isinstance(schema, dict):
                    print(f"Keys in schema: {list(schema.keys())}")
                elif isinstance(schema, list):
                    print(f"Schema is a list with {len(schema)} items")
                    if len(schema) > 0:
                        print(f"First item keys: {list(schema[0].keys()) if isinstance(schema[0], dict) else 'N/A'}")
                print(f"\nFull response (first 500 chars): {str(schema)[:500]}")
                
        except Exception as e:
            print(f"Error retrieving attributes: {e}")
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
        
        Args:
            assets: List of asset dictionaries (from HostAsset.dict())
        """
        logger.info(f"Syncing {len(assets)} assets to Jira")
        results = {"total": len(assets), "created": 0, "updated": 0, "errors": 0, "error_details": []}

        # Import mapping functions once
        from src.core.models.jira_model import map_host_to_jira, map_linux_to_jira, map_windows_to_jira, map_sparc_to_jira

        for asset_data in assets:
            try:
                # Convert dict back to HostAsset model for type checking
                asset_model = HostAsset(**asset_data)
                hostname = asset_model.hostname
                
                logger.info(f"Preparing to create/update asset in Jira for: {hostname}")
                
                existing_asset_id = self.find_asset_by_hostname(hostname)
                
                # Use the appropriate mapping function based on asset type
                if hasattr(asset_model, 'type'):
                    if asset_model.type == 'linux':
                        jira_payload = map_linux_to_jira(asset_model)
                    elif asset_model.type == 'windows':
                        jira_payload = map_windows_to_jira(asset_model)
                    elif asset_model.type == 'sparc':
                        jira_payload = map_sparc_to_jira(asset_model)
                    else:
                        jira_payload = map_host_to_jira(asset_model)
                else:
                    jira_payload = map_host_to_jira(asset_model)

                if existing_asset_id:
                    logger.info(f"Updating asset in Jira: {hostname} (ID: {existing_asset_id})")
                    # Remove objectTypeId from update payload to avoid constraint violation
                    update_payload = jira_payload.copy()
                    if "objectTypeId" in update_payload:
                        del update_payload["objectTypeId"]
                    
                    # Filter out attributes that might not exist on the existing object type
                    # Keep only basic attributes that should exist on most object types
                    safe_attributes = []
                    for attr in update_payload.get("attributes", []):
                        attr_id = attr.get("objectTypeAttributeId")
                        # Only include basic attributes that are likely to exist
                        if attr_id in ["100", "121", "189", "190", "191"]:  # Name, IP, CPU Cores, CPU Model, Memory
                            safe_attributes.append(attr)
                    
                    update_payload["attributes"] = safe_attributes
                    logger.info(f"Updating with {len(safe_attributes)} safe attributes")
                    
                    self.update_asset(existing_asset_id, update_payload)
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
    
