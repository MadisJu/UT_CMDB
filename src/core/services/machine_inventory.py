"""
Functions that use the parsed ansible inventory from config.py
"""

import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.core.configs.config import settings

logger = logging.getLogger(__name__)


class MachineInventory:
    """"""

    def __init__(self, parsed_inventory=None):
        """
        Parsed_inv is already preparsed inv, otherwise just idk takes the settings one
        """
        self.inventory = parsed_inventory or settings.get_ansible_inventory()
        logger.info(self.inventory)

    def get_all_machines(self) -> List[str]:
        """Return all hostnames in the inventory."""
        hosts = self.inventory.get("all", {}).get("hosts", [])
        return list(hosts)

    def get_machines_by_group(self, group: str) -> List[str]:
        """Return all hosts in a specific group."""
        group_data = self.inventory.get(group, {})
        hosts = group_data.get("hosts", [])
        return list(hosts)

    def get_host_vars(self, host: str) -> Dict[str, Any]:
        """RETURN HOST VARIABLES LIKE IP AND SHI"""
        result = {}

        for group_data in self.inventory.values():
            hosts = group_data.get("hosts", {})
            if host in hosts:
                result.update(hosts[host])

        return result

    def get_target_hosts_with_users(
        self, group: Optional[str] = None, default_user: str = "root"
    ) -> List[Tuple[str, str]]:
        """
        target hosts with users
        """
        hosts = self.get_machines_by_group(group) if group else self.get_all_machines()
        result = []

        for host in hosts:
            host_vars = self.get_host_vars(host)
            user = host_vars.get("ansible_user", default_user)
            result.append((host, user))

        return result

    def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Return a summary similar to MachineInventory:
        - total hosts
        - number of hosts per group
        - number of hosts per OS type (if ansible_distribution available)
        """
        all_hosts = self.get_all_machines()
        group_counts = {group: len(data.get("hosts", [])) 
                        for group, data in self.inventory.items() if group != "_meta"}

        os_counts = {}
        for host in all_hosts:
            facts = self.get_host_vars(host)
            distro = facts.get("ansible_distribution", "unknown")
            os_counts[distro] = os_counts.get(distro, 0) + 1

        return {
            "total_hosts": len(all_hosts),
            "group_counts": group_counts,
            "os_counts": os_counts
        }

    def get_host_info(self, host: str) -> Dict[str, Any]:
        """Return hostvars for a specific host."""
        return self.get_host_vars(host)