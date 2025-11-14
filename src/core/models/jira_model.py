from src.core.models.asset_model import HostAsset
from src.core.services.jira_field_mapper_service import JiraFieldMapper

jira_mapper = JiraFieldMapper()

def map_host_to_jira(asset: HostAsset) -> dict:
    """
    Map a generic host asset to Jira dynamically.
    """

    return jira_mapper.map_asset(asset)

def map_linux_to_jira(asset: HostAsset) -> dict:
    return jira_mapper.map_asset(asset)

def map_windows_to_jira(asset: HostAsset) -> dict:
    return jira_mapper.map_asset(asset)

def map_sparc_to_jira(asset: HostAsset) -> dict:
    return jira_mapper.map_asset(asset)
