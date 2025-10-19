from src.core.plugins.base_plugin import BasePlugin
from src.core.configs.config import settings
from src.core.models.fact_parser import parse_facts_to_asset
from pathlib import Path
import logging
import json
from typing import Dict, Any
import platform
import subprocess
import ansible_runner

logger = logging.getLogger(__name__)


class AnsiblePlugin(BasePlugin):
    name = "ansible"
    description = "Fetches host facts via Ansible"

    def __init__(self):
        import tempfile
        # Use system temp directory for cross-platform compatibility
        temp_dir = Path(tempfile.gettempdir())
        self.private_data_dir = temp_dir / "ansible_runner"
        self.private_data_dir.mkdir(exist_ok=True)
        
        # Create minimal inventory structure
        self.inventory_dir = self.private_data_dir / "inventory"
        self.inventory_dir.mkdir(exist_ok=True)
        
        # Check if Ansible is available
        self._check_ansible_availability()
        
        # Create ansible.cfg
        self._create_ansible_config()

    def _check_ansible_availability(self):
        """Check if Ansible is available in the system PATH."""
        try:
            result = subprocess.run(
                ["ansible", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("Ansible is not properly installed or configured")
                self.ansible_available = False
            else:
                logger.info("Ansible is available")
                self.ansible_available = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Ansible command not found in PATH. Please install Ansible.")
            self.ansible_available = False

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
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o AddressFamily=inet
pipelining = True
"""
        ansible_cfg.write_text(config_content)

    def discover(self, target: str, user: str = "root") -> Dict[str, Any]:
        """
        Discover a single host using Ansible.
        
        Args:
            target: Host IP or hostname to discover
            user: The user to connect with
            
        Returns:
            Dictionary containing host facts
        """
        try:
            logger.info(f"Starting Ansible discovery for {target}")
            
            # Check if Ansible is available
            if not self.ansible_available:
                logger.warning(f"Ansible not available, using fallback facts for {target}")
                fallback_facts = self._create_fallback_facts(target)
                asset = parse_facts_to_asset(fallback_facts)
                return asset.model_dump()
            
            facts = self._run_ansible_setup(target, user)
            
            if facts:
                logger.info(f"Successfully discovered {target}")
                asset = parse_facts_to_asset(facts)
                return asset.model_dump()
            else:
                logger.warning(f"Ansible discovery returned no facts for {target}, using fallback")
                fallback_facts = self._create_fallback_facts(target)
                asset = parse_facts_to_asset(fallback_facts)
                return asset.model_dump()
                
        except Exception as e:
            logger.error(f"Error during Ansible discovery for {target}: {e}")
            fallback_facts = self._create_fallback_facts(target)
            asset = parse_facts_to_asset(fallback_facts)
            return asset.model_dump()

    def discover_all(self, targets: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Discover multiple hosts using Ansible.
        
        Args:
            targets: List of host IPs or hostnames
            
        Returns:
            Dictionary mapping hostnames to their facts
        """
        results = {}
        
        try:
            logger.info(f"Starting Ansible discovery for {len(targets)} hosts")
            
            for target in targets:
                try:
                    facts = self._run_ansible_setup(target, "root")
                    if facts:
                        asset = parse_facts_to_asset(facts)
                        results[target] = asset.model_dump()
                    else:
                        fallback_facts = self._create_fallback_facts(target)
                        asset = parse_facts_to_asset(fallback_facts)
                        results[target] = asset.model_dump()
                except Exception as e:
                    logger.error(f"Failed to discover {target}: {e}")
                    fallback_facts = self._create_fallback_facts(target)
                    asset = parse_facts_to_asset(fallback_facts)
                    results[target] = asset.model_dump()
            
            logger.info(f"Completed discovery for {len(targets)} hosts")
                    
        except Exception as e:
            logger.error(f"Error during batch Ansible discovery: {e}")

            for target in targets:
                fallback_facts = self._create_fallback_facts(target)
                asset = parse_facts_to_asset(fallback_facts)
                results[target] = asset.model_dump()
        
        return results

    def _run_ansible_setup(self, target: str, user: str) -> Dict[str, Any]:
        """Run ansible setup module using subprocess for Windows compatibility."""
        try:
            inventory_file = self.inventory_dir / f"{target.replace('.', '_')}.ini"
            inventory_content = f"""[all]
{target} ansible_host={target} ansible_user={user}
"""
            inventory_file.write_text(inventory_content)
            logger.debug(f"Ansible inventory file: {inventory_file}")
            try:
                logger.debug(f"Inventory contents:\n{inventory_file.read_text()} ")
            except Exception:
                pass

            cmd = [
                "ansible",
                "-i", str(inventory_file),
                "all",
                "-m", "setup",
                "--one-line",
                "-o",
                "-vvvv"  # verbose for debugging SSH connectivity
            ]
            
            # Avoid remote python interpreter auto-discovery by setting a common path
            # If your remote uses a different path, expose it via settings and pass here
            cmd.extend(["-e", "ansible_python_interpreter=/usr/bin/python3"])
            
            logger.debug(f"Running ansible command: {' '.join(cmd)}")
            

            result = subprocess.run(
                cmd,
                cwd=str(self.private_data_dir),
                capture_output=True,
                text=True,
                timeout=settings.ansible_timeout
            )
            
            if result.returncode == 0:
                facts = self._parse_ansible_output(result.stdout, target)
                return facts
            else:
                logger.error(
                    "Ansible command failed for %s: rc=%s\nSTDOUT:\n%s\nSTDERR:\n%s",
                    target,
                    result.returncode,
                    (result.stdout or "<empty>"),
                    (result.stderr or "<empty>")
                )
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Ansible command timed out for {target}")
            return None
        except Exception as e:
            logger.error(f"Error running ansible for {target}: {e}")
            return None

    def _parse_ansible_output(self, output: str, target: str) -> Dict[str, Any]:
        """Parse ansible output to extract facts."""
        try:

            lines = output.strip().split('\n')
            facts = {}
            
            for line in lines:
                if not line.strip():
                    continue
                    
                if '|' in line and '=>' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        hostname = parts[0].strip()
                        fact_part = parts[1].split('=>', 1)
                        if len(fact_part) >= 2:
                            try:
                                json_str = fact_part[1].strip()
                                parsed_facts = json.loads(json_str)
                                
                                if 'ansible_facts' in parsed_facts:
                                    facts.update(parsed_facts['ansible_facts'])
                                
                                for key, value in parsed_facts.items():
                                    if key != 'ansible_facts':
                                        facts[key] = value
                                        
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON from ansible output: {e}")
                                continue
            
            if not facts:
                logger.warning(f"No facts parsed from ansible output for {target}")
                fallback_facts = self._create_fallback_facts(target)
                asset = parse_facts_to_asset(fallback_facts)
                return asset.model_dump()
            
            facts.update({
                "discovery_status": "success",
                "discovery_method": "ansible_subprocess"
            })
            
            asset = parse_facts_to_asset(facts)
            return asset.model_dump()
            
        except Exception as e:
            logger.error(f"Error parsing ansible output for {target}: {e}")
            fallback_facts = self._create_fallback_facts(target)
            asset = parse_facts_to_asset(fallback_facts)
            return asset.model_dump()

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