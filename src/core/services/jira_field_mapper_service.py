import json
from pathlib import Path
from typing import Dict, Any, Optional, Type, List
import logging

from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.core.integrations.jira_client import JiraClient
from src.core.logging_adapter import audit_log

logger = logging.getLogger(__name__)

os_field_sets: Dict[str, Type[HostAsset]] = {
    "server": HostAsset,      # base server fields
    "linux": LinuxAsset,      # linux-specific fields
    "windows": WindowsAsset,  # windows-specific fields
    "sparc": SparcAsset       # sparc-specific fields
}

os_object_type_ids: Dict[str, str] = {
    "server": "12",
    "linux": "13",
    "windows": "14",
    "sparc": "27"
}

class JiraFieldMapper:
    def __init__(self, mapping_file: str = "src/core/configs/jira_field_map.json"):
        self.mapping_file = Path(mapping_file)
        self.jira = JiraClient()
        self.field_map: Dict[str, str] = {}
        self.load_mapping()
        # self.ensure_all_attributes() # Disabled automatic creation

    def load_mapping(self):
        if self.mapping_file.exists():
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                self.field_map = json.load(f)
        else:
            self.field_map = {}

    def save_mapping(self):
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.field_map, f, indent=4)

    def ensure_attribute(self, field_name: str, object_type: str = "server") -> str:
        """Return objectTypeAttributeId, create attribute if missing."""
        key = f"{object_type}.{field_name}"
        
        if key in self.field_map:
            return self.field_map[key]

        attr_data = {
            "name": field_name,
            "type": "TEXT",
            "description": f"Automatically created for field {field_name}",
            "objectTypeId": os_object_type_ids[object_type]
        }
        logger.info(f"Creating attribute for key: {attr_data}")
        created_attr = self.jira.create_attribute(attr_data, object_type_id=os_object_type_ids[object_type])
        attr_id = created_attr.get("id") or created_attr.get("objectTypeAttributeId")
        if not attr_id:
            raise RuntimeError(f"Failed to get ID for attribute {field_name}")

        self.field_map[key] = attr_id
        self.save_mapping()
        return attr_id

    def ensure_all_attributes(self):
        """Ensure all fields for all object types."""
        for object_type, model_cls in os_field_sets.items():

            base_fields = os_field_sets["server"].__fields__

            for field_name, field in model_cls.__fields__.items():

                # Skip inherited server fields for OS types
                if object_type != "server" and field_name in base_fields:
                    continue

                try:
                    self.ensure_attribute(field_name, object_type=object_type)
                except Exception as e:
                    logger.warning(
                        f"Could not ensure attribute {field_name} for {object_type}: {e}"
                    )

    def map_asset(self, asset: HostAsset) -> List[Dict[str, Any]]:
        """Return Jira payloads for base + OS-specific objects."""
        os_type = getattr(asset, "type", "server").lower()
        object_type_id = os_object_type_ids.get(os_type, os_object_type_ids["server"])

        # Combine server + OS-specific fields
        all_fields = {}
        all_fields.update(os_field_sets["server"].__fields__)
        if os_type != "server" and os_type in os_field_sets:
            os_fields = {
                k: v for k, v in os_field_sets[os_type].__fields__.items()
                if k not in all_fields
            }
            all_fields.update(os_fields)

        attributes = []
        for field_name in all_fields:
            value = getattr(asset, field_name, None)
            if value is not None:
                # Determine the object type for field mapping
                field_object_type = "server" if field_name in os_field_sets["server"].__fields__ else os_type
                attr_id = self.ensure_attribute(field_name, object_type=field_object_type)

                # Wrap the value in objectAttributeValues
                attributes.append({
                    "objectTypeAttributeId": attr_id,
                    "objectAttributeValues": [{"value": value}]
                })

        return {
            "label": getattr(asset, "hostname", "unknown"),
            "objectTypeId": object_type_id,
            "attributes": attributes
        }