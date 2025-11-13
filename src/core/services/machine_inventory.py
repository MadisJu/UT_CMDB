"""
Machine inventory service for managing configured machines for discovery.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.core.configs.config import settings

logger = logging.getLogger(__name__)


class MachineInventory:
    """Service for managing machine inventory configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or settings.address_book_path
        self._config_cache = None
        self._last_modified = None
    
    def _load_config(self) -> Dict[str, Any]:
        try:
            current_modified = self.config_path.stat().st_mtime if self.config_path.exists() else 0
            
            if self._config_cache is None or current_modified > self._last_modified:
                if not self.config_path.exists():
                    logger.warning(f"Configuration file not found: {self.config_path}")
                    return self._get_default_config()
                
                with self.config_path.open('r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                self._last_modified = current_modified
                logger.info(f"Loaded machine inventory configuration from {self.config_path}")
            
            return self._config_cache
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return { # see osa hardcoded, tuleb muuta hiljem
            "all": [
                {
                    "hostname": "25.44.45.59",
                    "ip_address": "25.44.45.59",
                    "user": "chronia",
                    "type": "linux",
                    "description": "Primary server",
                    "enabled": True
                }
            ],
            "categorized": {
                "linux_servers": [
                    {
                        "hostname": "25.44.45.59",
                        "ip_address": "25.44.45.59",
                        "user": "chronia",
                        "type": "linux",
                        "description": "Primary Linux server",
                        "enabled": True
                    }
                ],
                "windows_servers": [],
                "network_devices": [],
                "other_devices": []
            },
            "discovery_settings": {
                "default_user": "chronia",
                "timeout": 300,
                "retry_count": 3,
                "parallel_discovery": True,
                "max_parallel_hosts": 5
            }
        }
    
    def get_all_machines(self) -> List[Dict[str, Any]]:
        
        config = self._load_config()
        return config.get("all", [])
    
    def get_enabled_machines(self) -> List[Dict[str, Any]]:
        
        machines = self.get_all_machines()
        return [machine for machine in machines if machine.get("enabled", True)]
    
    def get_machines_by_type(self, machine_type: str) -> List[Dict[str, Any]]:
        
        machines = self.get_enabled_machines()
        return [machine for machine in machines if machine.get("type", "").lower() == machine_type.lower()]
    
    def get_machines_by_category(self, category: str) -> List[Dict[str, Any]]:
        
        config = self._load_config()
        categorized = config.get("categorized", {})
        return categorized.get(category, [])
    
    def get_machine_by_hostname(self, hostname: str) -> Optional[Dict[str, Any]]:
        
        machines = self.get_all_machines()
        for machine in machines:
            if machine.get("hostname") == hostname or machine.get("ip_address") == hostname:
                return machine
        return None
    
    def get_discovery_settings(self) -> Dict[str, Any]:
        
        config = self._load_config()
        return config.get("discovery_settings", {})
    
    def get_target_hosts(self) -> List[str]:
        
        machines = self.get_enabled_machines()
        return [machine.get("ip_address") or machine.get("hostname") for machine in machines]
    
    def get_target_hosts_with_users(self) -> List[tuple]:
        
        machines = self.get_enabled_machines()
        discovery_settings = self.get_discovery_settings()
        default_user = discovery_settings.get("default_user", "root")
        
        result = []
        for machine in machines:
            host = machine.get("ip_address") or machine.get("hostname")
            user = machine.get("user") or default_user
            result.append((host, user))
        
        return result
    
    def add_machine(self, machine_config: Dict[str, Any]) -> bool:
        
        try:
            config = self._load_config()
            
            # Validate required fields
            required_fields = ["hostname", "ip_address"]
            for field in required_fields:
                if field not in machine_config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Add to all machines
            if "all" not in config:
                config["all"] = []
            
            config["all"].append(machine_config)
            
            # Add to appropriate category
            machine_type = machine_config.get("type", "other")
            category_map = {
                "linux": "linux_servers",
                "windows": "windows_servers",
                "network": "network_devices",
                "other": "other_devices"
            }
            
            category = category_map.get(machine_type.lower(), "other_devices")
            if "categorized" not in config:
                config["categorized"] = {}
            if category not in config["categorized"]:
                config["categorized"][category] = []
            
            config["categorized"][category].append(machine_config)
            
            self._save_config(config)
            logger.info(f"Added machine: {machine_config['hostname']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add machine: {e}")
            return False
    
    def remove_machine(self, hostname: str) -> bool:
        
        try:
            config = self._load_config()
            
            if "all" in config:
                config["all"] = [m for m in config["all"] 
                               if m.get("hostname") != hostname and m.get("ip_address") != hostname]
            
            if "categorized" in config:
                for category, machines in config["categorized"].items():
                    config["categorized"][category] = [m for m in machines 
                                                   if m.get("hostname") != hostname and m.get("ip_address") != hostname]
            
            self._save_config(config)
            logger.info(f"Removed machine: {hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove machine: {e}")
            return False
    
    def update_machine(self, hostname: str, updates: Dict[str, Any]) -> bool:
        
        try:
            config = self._load_config()
            updated = False
            
            if "all" in config:
                for machine in config["all"]:
                    if machine.get("hostname") == hostname or machine.get("ip_address") == hostname:
                        machine.update(updates)
                        updated = True
                        break
            
            if "categorized" in config:
                for category, machines in config["categorized"].items():
                    for machine in machines:
                        if machine.get("hostname") == hostname or machine.get("ip_address") == hostname:
                            machine.update(updates)
                            updated = True
                            break
            
            if updated:
                self._save_config(config)
                logger.info(f"Updated machine: {hostname}")
                return True
            else:
                logger.warning(f"Machine not found: {hostname}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update machine: {e}")
            return False
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.config_path.open('w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._config_cache = None
            logger.info(f"Saved configuration to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        
        config = self._load_config()
        all_machines = config.get("all", [])
        enabled_machines = [m for m in all_machines if m.get("enabled", True)]
        
        type_counts = {}
        for machine in enabled_machines:
            machine_type = machine.get("type", "unknown")
            type_counts[machine_type] = type_counts.get(machine_type, 0) + 1
        
        category_counts = {}
        categorized = config.get("categorized", {})
        for category, machines in categorized.items():
            category_counts[category] = len(machines)
        
        return {
            "total_machines": len(all_machines),
            "enabled_machines": len(enabled_machines),
            "disabled_machines": len(all_machines) - len(enabled_machines),
            "type_counts": type_counts,
            "category_counts": category_counts,
            "discovery_settings": config.get("discovery_settings", {})
        }
