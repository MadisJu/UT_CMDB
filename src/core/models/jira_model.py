from src.core.models.asset_model import HostAsset


def map_host_to_jira(asset: HostAsset) -> dict:
    """
    Map a generic HostAsset to Jira format using a generic object type.
    This is a fallback for unknown asset types.
    """
    # Generic attribute mapping - you'll need to find the correct object type and attribute IDs
    # for your generic host object type in Jira
    return {
        "objectTypeId": "25",  # Generic hardware object type (placeholder)
        "attributes": [
            {"objectTypeAttributeId": "100", "objectAttributeValues": [{"value": asset.hostname}]},
            {"objectTypeAttributeId": "121", "objectAttributeValues": [{"value": asset.ip_address}]},
        ]
    }


def map_linux_to_jira(asset):
    """
    Map Linux asset to Jira format using object type 13.
    Uses the correct attribute IDs discovered from the Jira API.
    """
    # Real attribute IDs from Jira object type 
    name_field_id = "100"           # Name
    ip_address_field_id = "121"      # IP Address  
    os_version_field_id = "115"      # OS Version
    asset_status_field_id = "114"    # Asset Status
    operational_status_field_id = "117"  # Operational Status
    status_field_id = "118"          # Status
    asset_tag_field_id = "101"       # Asset Tag
    serial_number_field_id = "102"   # Serial Number
    model_name_field_id = "103"      # Model Name
    device_type_field_id = "113"     # Device Type
    support_group_field_id = "116"   # Support Group
    owner_group_field_id = "112"     # Owner Group
    domain_name_field_id = "122"     # Domain Name
    cpu_cores_field_id = "189"       # CPU Cores (Physical cores)
    cpu_model_field_id = "190"       # CPU Model
    memory_field_id = "191"          # Memory

    attributes = [
        {"objectTypeAttributeId": name_field_id, "objectAttributeValues": [{"value": asset.hostname}]},
        {"objectTypeAttributeId": ip_address_field_id, "objectAttributeValues": [{"value": asset.ip_address}]},
    ]
    
    if hasattr(asset, 'cpu_cores') and asset.cpu_cores:
        attributes.append({"objectTypeAttributeId": cpu_cores_field_id, "objectAttributeValues": [{"value": str(asset.cpu_cores)}]})
    
    if hasattr(asset, 'metadata') and asset.metadata and 'processor_model' in asset.metadata:
        attributes.append({"objectTypeAttributeId": cpu_model_field_id, "objectAttributeValues": [{"value": asset.metadata['processor_model']}]})
    
    if hasattr(asset, 'memory_mb') and asset.memory_mb:
        memory_gb = round(asset.memory_mb / 1024, 2)
        attributes.append({"objectTypeAttributeId": memory_field_id, "objectAttributeValues": [{"value": f"{memory_gb} GB"}]})
    
    if hasattr(asset, 'os') and asset.os:
        attributes.append({"objectTypeAttributeId": os_version_field_id, "objectAttributeValues": [{"value": asset.os}]})
    if hasattr(asset, 'domain_name') and asset.domain_name:
        attributes.append({"objectTypeAttributeId": domain_name_field_id, "objectAttributeValues": [{"value": asset.domain_name}]})
    if hasattr(asset, 'asset_tag') and asset.asset_tag:
        attributes.append({"objectTypeAttributeId": asset_tag_field_id, "objectAttributeValues": [{"value": asset.asset_tag}]})
    if hasattr(asset, 'serial_number') and asset.serial_number:
        attributes.append({"objectTypeAttributeId": serial_number_field_id, "objectAttributeValues": [{"value": asset.serial_number}]})
    if hasattr(asset, 'model_name') and asset.model_name:
        attributes.append({"objectTypeAttributeId": model_name_field_id, "objectAttributeValues": [{"value": asset.model_name}]})
    if hasattr(asset, 'device_type') and asset.device_type:
        attributes.append({"objectTypeAttributeId": device_type_field_id, "objectAttributeValues": [{"value": asset.device_type}]})
    if hasattr(asset, 'support_group') and asset.support_group:
        attributes.append({"objectTypeAttributeId": support_group_field_id, "objectAttributeValues": [{"value": asset.support_group}]})
    if hasattr(asset, 'owner_group') and asset.owner_group:
        attributes.append({"objectTypeAttributeId": owner_group_field_id, "objectAttributeValues": [{"value": asset.owner_group}]})
    
    attributes.append({"objectTypeAttributeId": asset_status_field_id, "objectAttributeValues": [{"value": "In Use"}]})
    attributes.append({"objectTypeAttributeId": operational_status_field_id, "objectAttributeValues": [{"value": "Active"}]})
    attributes.append({"objectTypeAttributeId": status_field_id, "objectAttributeValues": [{"value": "Active"}]})

    return {
        "objectTypeId": "13",
        "attributes": attributes
    }


def map_windows_to_jira(asset):
    """Map Windows asset to Jira format - same as generic host for now"""
    return map_host_to_jira(asset)


def map_sparc_to_jira(asset):
    """Map SPARC asset to Jira format - same as generic host for now"""
    return map_host_to_jira(asset)
