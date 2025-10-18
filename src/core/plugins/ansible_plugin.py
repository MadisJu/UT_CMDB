from src.core.plugins.base_plugin import BasePlugin
from src.core.configs.config import settings
import ansible_runner
from pathlib import Path
import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnsiblePlugin(BasePlugin):
    name = "ansible"
    description = "Fetches host facts via Ansible"

    def __init__(self):
        self.private_data_dir = Path("/tmp/ansible_runner")
        self.private_data_dir.mkdir(exist_ok=True)
        
        # Create minimal inventory structure
        self.inventory_dir = self.private_data_dir / "inventory"
        self.inventory_dir.mkdir(exist_ok=True)
        
        # Create ansible.cfg
        self._create_ansible_config()

    def _create_ansible_config(self):
        """Create ansible.cfg for proper configuration."""
        ansible_cfg = self.private_data_dir / "ansible.cfg"
        config_content = f"""[defaults]
host_key_checking = False
timeout = {settings.ansible_timeout}
gathering = smart
fact_caching = jsonfile
fact_caching_connection = {self.private_data_dir}/fact_cache
fact_caching_timeout = 86400

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no
pipelining = True
"""
        ansible_cfg.write_text(config_content)

    def discover(self, target: str, user: str = None) -> Dict[str, Any]:
        """
        Discover a single host using Ansible.
        
        Args:
            target: Host IP or hostname to discover
            user: SSH user for connection (optional)
            
        Returns:
            Dictionary containing host facts
        """
        try:
            # Create inventory file for this target
            inventory_file = self.inventory_dir / f"{target.replace('.', '_')}.ini"
            inventory_content = f"""[all]
{target} ansible_host={target} ansible_user={user or 'root'}
"""
            inventory_file.write_text(inventory_content)

            logger.info(f"Starting Ansible discovery for {target}")
            
            # Run Ansible setup module
            r = ansible_runner.run(
                private_data_dir=str(self.private_data_dir),
                inventory=str(inventory_file),
                module="setup",
                host_pattern="all",
                extravars={"ansible_user": user or "root"},
                quiet=True,
                suppress_ansible_output=True
            )
            
            if r.status == "successful":
                # Get facts from the result
                facts = self._extract_facts_from_result(r, target)
                logger.info(f"Successfully discovered {target}")
                return facts
            else:
                logger.error(f"Ansible discovery failed for {target}: {r.stderr}")
                return self._create_fallback_facts(target)
                
        except Exception as e:
            logger.error(f"Error during Ansible discovery for {target}: {e}")
            return self._create_fallback_facts(target)

    def discover_all(self, targets: List[str], user: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Discover multiple hosts using Ansible.
        
        Args:
            targets: List of host IPs or hostnames
            user: SSH user for connection (optional)
            
        Returns:
            Dictionary mapping hostnames to their facts
        """
        results = {}
        
        # Create inventory file for all targets
        inventory_file = self.inventory_dir / "multi_host.ini"
        inventory_content = "[all]\n"
        for target in targets:
            inventory_content += f"{target} ansible_host={target} ansible_user={user or 'root'}\n"
        
        inventory_file.write_text(inventory_content)
        
        try:
            logger.info(f"Starting Ansible discovery for {len(targets)} hosts")
            
            # Run Ansible setup module for all hosts
            r = ansible_runner.run(
                private_data_dir=str(self.private_data_dir),
                inventory=str(inventory_file),
                module="setup",
                host_pattern="all",
                extravars={"ansible_user": user or "root"},
                quiet=True,
                suppress_ansible_output=True
            )
            
            if r.status == "successful":
                # Extract facts for each host
                for target in targets:
                    facts = self._extract_facts_from_result(r, target)
                    results[target] = facts
                logger.info(f"Successfully discovered {len(targets)} hosts")
            else:
                logger.error(f"Ansible discovery failed: {r.stderr}")
                # Create fallback facts for all targets
                for target in targets:
                    results[target] = self._create_fallback_facts(target)
                    
        except Exception as e:
            logger.error(f"Error during batch Ansible discovery: {e}")
            # Create fallback facts for all targets
            for target in targets:
                results[target] = self._create_fallback_facts(target)
        
        return results

    def _extract_facts_from_result(self, result, target: str) -> Dict[str, Any]:
        """Extract facts from Ansible runner result."""
        try:
            # Get facts from the result events
            facts = {}
            for event in result.events:
                if event.get('event') == 'runner_on_ok':
                    event_data = event.get('event_data', {})
                    if event_data.get('host') == target:
                        facts = event_data.get('res', {}).get('ansible_facts', {})
                        break
            
            # If no facts found in events, try to get from fact cache
            if not facts:
                fact_cache_file = self.private_data_dir / "fact_cache" / target
                if fact_cache_file.exists():
                    facts = json.loads(fact_cache_file.read_text())
            
            return facts if facts else self._create_fallback_facts(target)
            
        except Exception as e:
            logger.error(f"Error extracting facts for {target}: {e}")
            return self._create_fallback_facts(target)

    def _create_fallback_facts(self, target: str) -> Dict[str, Any]:
        """Create fallback facts when Ansible discovery fails."""
        return {
            "ansible_hostname": target,
            "ansible_default_ipv4": {"address": target},
            "ansible_distribution": "Unknown",
            "ansible_os_family": "Unknown",
            "ansible_architecture": "Unknown",
            "ansible_processor_vcpus": 1,
            "ansible_memtotal_mb": 1024,
            "ansible_kernel": "Unknown",
            "ansible_distribution_version": "Unknown",
            "ansible_facts": {"packages": []},
            "ansible_hotfixes": [],
            "ansible_ip_addresses": [target],
            "ansible_os_name": "Unknown",
            "discovery_status": "failed",
            "discovery_method": "fallback"
        }