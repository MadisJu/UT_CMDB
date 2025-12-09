import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urlparse
from src.api.schemas.jira import JiraAsset, JiraAssetAttribute, JiraAQLResponse
from src.core.configs.config import Settings
from src.core.models.fact_parser import parse_facts_to_asset
from src.core.models.asset_model import HostAsset 

logger = logging.getLogger(__name__)


class JiraClient:  

    def __init__(self, settings: Optional[Settings] = None):
        if settings is None:
            from src.core.configs.config import settings as global_settings
            settings = global_settings
            
        self.email = settings.jira_user_email
        self.token = settings.jira_api_token
        self.cloud_id = settings.jira_cloud_id
        self.workspace_id = settings.jira_asset_workspace_id
        self.proxies = self._build_proxy_config(
            settings.jira_proxy_url,
            settings.jira_proxy_username,
            settings.jira_proxy_password,
        )
        
        if not all([self.email, self.token, self.cloud_id, self.workspace_id]):
            raise ValueError("Jira credentials, cloud ID, and workspace ID must be set in settings.")

        self.base_url = f"https://api.atlassian.com/ex/jira/{self.cloud_id}/jsm/assets/workspace/{self.workspace_id}/v1"
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if self.proxies:
            logger.info("Jira client configured to use proxy settings.")

    @staticmethod
    def _build_proxy_config(proxy_url: Optional[str], username: Optional[str], password: Optional[str]) -> Optional[Dict[str, str]]:
        if not proxy_url:
            return None

        if "://" not in proxy_url:
            proxy_url = f"http://{proxy_url}"

        if username:
            parsed = urlparse(proxy_url)
            host = parsed.hostname or parsed.netloc
            port = f":{parsed.port}" if parsed.port else ""
            user_info = f"{username}:{password or ''}@"
            netloc = f"{user_info}{host}{port}"
            proxy_url = parsed._replace(netloc=netloc, path="", params="", query="", fragment="").geturl()

        return {"http": proxy_url, "https": proxy_url}

    def _request(self, method: str, url: str, **kwargs):
        request_kwargs = {"headers": self.headers, "auth": self.auth}
        if self.proxies:
            request_kwargs["proxies"] = self.proxies
        request_kwargs.update(kwargs)
        return requests.request(method, url, **request_kwargs)
    
    def query_assets(self, aql_query: str = "ObjectType = \"Servers\"", results_per_page: int = 50) -> List[JiraAsset]:
        endpoint = f"{self.base_url}/aql/objects"
        params = {"qlQuery": aql_query, "resultsPerPage": results_per_page}
        
        try:
            logger.info(f"Querying Jira assets with AQL: {aql_query}")
            response = self._request("get", endpoint, params=params)
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
        endpoint = f"{self.base_url}/objectschema/list"
        
        try:
            logger.info("Fetching Jira asset schemas")
            response = self._request("get", endpoint)
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

        endpoint = f"{self.base_url}/objectschema/list"
        
        try:
            logger.info(f"Fetching all object schemas to find attributes for type ID: {object_type_id}")
            response = self._request("get", endpoint)
            response.raise_for_status()
            
            all_schemas = response.json()
            
            print(f"Response type: {type(all_schemas)}")
            if isinstance(all_schemas, dict):
                print(f"Response keys: {list(all_schemas.keys())}")
            elif isinstance(all_schemas, list):
                print(f"Response length: {len(all_schemas)}")
                if len(all_schemas) > 0:
                    print(f"First item type: {type(all_schemas[0])}")
                    print(f"First item keys: {list(all_schemas[0].keys()) if isinstance(all_schemas[0], dict) else 'N/A'}")
            
            schemas_to_search = []
            if isinstance(all_schemas, dict):
                if 'values' in all_schemas:
                    schemas_to_search = all_schemas['values']
                elif 'objectTypes' in all_schemas:
                    schemas_to_search = [all_schemas]
                elif 'schemas' in all_schemas:
                    schemas_to_search = all_schemas['schemas']
                else:
                    for key, value in all_schemas.items():
                        if isinstance(value, dict) and 'objectTypes' in value:
                            schemas_to_search.append(value)
                        elif isinstance(value, list):
                            schemas_to_search.extend(value)
            elif isinstance(all_schemas, list):
                schemas_to_search = all_schemas
            
            print(f"Searching in {len(schemas_to_search)} schemas...")
            for i, schema in enumerate(schemas_to_search):
                print(f"Schema {i}: ID={schema.get('id')}, Name={schema.get('name')}")
                
                if isinstance(schema, dict) and 'id' in schema:
                    schema_id = schema['id']
                    try:
                    
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
                                schema_response = self._request("get", endpoint)
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
                                try:

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
                                            attr_response = self._request("get", endpoint)
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
    
    def list_object_attributes(self, object_type_id: str = "25"):
        print("START METHOD", flush=True)
        try:
            schema = self.get_object_type_schema(object_type_id)
            
            print(f"\n=== Attributes for Object Type {object_type_id} ===\n")
            
            attributes = None
            if isinstance(schema, list):
                attributes = schema
                print(f"Found {len(attributes)} attributes in direct list")
            elif isinstance(schema, dict):
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

        endpoint = f"{self.base_url}/object/create"
        logger.info("creating asset to " + endpoint)
        
        try:
            logger.info(f"Creating asset in Jira: {asset_data.get('label', 'Unknown')}")
            response = self._request("post", endpoint, json=asset_data)
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

        endpoint = f"{self.base_url}/object/{asset_id}" 
        
        try:
            logger.info(f"Updating asset in Jira: {asset_id}")
            response = self._request("put", endpoint, json=asset_data)
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

    
        endpoint = f"{self.base_url}/object/{asset_id}"
        
        try:
            logger.info(f"Deleting asset from Jira: {asset_id}")
            response = self._request("delete", endpoint)
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

        endpoint = f"{self.base_url}/object/{asset_id}" 
        
        try:
            logger.info(f"Retrieving asset from Jira: {asset_id}")
            response = self._request("get", endpoint)
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

        logger.info(f"Syncing {len(assets)} assets to Jira")
        results = {"total": len(assets), "created": 0, "updated": 0, "errors": 0, "error_details": []}

        from src.core.models.jira_model import map_host_to_jira, map_linux_to_jira, map_windows_to_jira, map_sparc_to_jira

        for asset_data in assets:
            try:
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
                    update_payload = jira_payload.copy()
                    if "objectTypeId" in update_payload:
                        del update_payload["objectTypeId"]

                    safe_attributes = []
                    for attr in update_payload.get("attributes", []):
                        attr_id = attr.get("objectTypeAttributeId")
                        if attr_id in ["100", "121", "189", "190", "191"]: 
                            safe_attributes.append(attr)
                    
                    update_payload["attributes"] = safe_attributes
                    logger.info(f"Updating with {len(safe_attributes)} safe attributes")
                    
                    self.update_asset(existing_asset_id, update_payload)
                    results["updated"] += 1
                    logger.info(f"Successfully updated asset for hostname {hostname}")
                else:
                    logger.info(f"Creating asset in Jira: {hostname.capitalize()}")
                    logger.info(f"Jira payload: {jira_payload}")
                    created_asset = self.create_asset(jira_payload)
                    results["created"] += 1
                    asset_key = created_asset.objectKey if created_asset else 'N/A'
                    logger.info(f"Successfully created asset {asset_key} for hostname {hostname}")

            except Exception as e:
                hostname_for_error = asset_data.get("hostname", "unknown")
                logger.error(f"Sync failed for {hostname_for_error}: {e}", exc_info=True)
                results["errors"] += 1
                results["error_details"].append(f"Sync failed for {hostname_for_error}: {e}")
        
        logger.info(f"Sync completed: {results['created']} created, {results['updated']} updated, {results['errors']} errors")
        return results
    
    def list_object_attributes2(self, object_type_id: str = "25") -> list[dict]:
        """
        Return all attribute definitions for a given object type.
        """
        endpoint = f"{self.base_url}/objecttype/{object_type_id}/attributes"
        response = self._request("get", endpoint)
        response.raise_for_status()
        return response.json()

    def create_attribute(self, attribute_payload: dict, object_type_id: str = "25") -> dict:
        """
        Create a new attribute for the obj whatever
        Example payload: {"name": "cpu_cores", "type": "STRING"}
        """
        endpoint = f"{self.base_url}/objecttype/{object_type_id}/attributes"
        response = self._request("post", endpoint, json=attribute_payload)
        response.raise_for_status()
        return response.json()
