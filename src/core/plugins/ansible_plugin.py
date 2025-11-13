from src.core.plugins.base_plugin import BasePlugin
from src.core.configs.config import settings
from pathlib import Path
import logging
import json
from typing import Dict, Any
import subprocess

logger = logging.getLogger(__name__)


class AnsiblePlugin(BasePlugin):
    name = "ansible"
    description = "Fetches host facts via Ansible"

    def __init__(self):
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        self.private_data_dir = temp_dir / "ansible_runner"
        self.private_data_dir.mkdir(exist_ok=True)
        
        self.inventory_dir = self.private_data_dir / "inventory"
        self.inventory_dir.mkdir(exist_ok=True)
        
        self._check_ansible_availability()
        self._create_ansible_config()

    def _check_ansible_availability(self):
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
        try:
            user = user or getattr(settings, "ansible_user", "root")
            logger.info(f"Starting Ansible discovery for {target} as user={user}")
            
            if not self.ansible_available:
                logger.warning(f"Ansible not available, using fallback for {target}")
                return self._create_fallback_facts(target)
            
            facts = self._run_ansible_setup(target, user)
            
            if not facts:
                logger.warning(f"Discovery failed for {target}, using fallback")
                return self._create_fallback_facts(target)

            logger.info(f"Successfully gathered facts for {target}")
            return facts
                
        except Exception as e:
            logger.error(f"Error during Ansible discovery for {target}: {e}")
            return self._create_fallback_facts(target)

    def _run_ansible_setup(self, target: str, user: str) -> Dict[str, Any]:
        try:
            inventory_file = self.inventory_dir / f"{target.replace('.', '_')}.ini"
            inventory_content = f"[all]\n{target} ansible_host={target} ansible_user={user}\n"
            inventory_file.write_text(inventory_content)

            cmd = [
                "ansible", "-i", str(inventory_file), "all",
                "-m", "setup", "-a", "gather_subset=all",
                "--one-line", "-o",
                "-e", "ansible_python_interpreter=/usr/bin/python3"
            ]
            
            logger.debug(f"Running ansible command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(self.private_data_dir),
                capture_output=True,
                text=True,
                timeout=settings.ansible_timeout
            )

            
            if result.returncode == 0:
                return self._parse_ansible_output(result.stdout, target)
            else:
                logger.error(
                    "Ansible command failed for %s: rc=%s\nSTDOUT:\n%s\nSTDERR:\n%s",
                    target, result.returncode, (result.stdout or "<empty>"), (result.stderr or "<empty>")
                )
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Ansible command timed out for {target}")
            return None
        except Exception as e:
            logger.error(f"Error running ansible for {target}: {e}")
            return None

    def _parse_ansible_output(self, output: str, target: str) -> Dict[str, Any]:
        try:
            lines = output.strip().split('\n')
            for line in lines:
                if '|' in line and '=>' in line:
                    parts = line.split('=>', 1)
                    if len(parts) > 1:
                        try:
                            facts = json.loads(parts[1].strip())
                            
                            if 'ansible_facts' in facts:
                                facts['ansible_facts']['discovery_status'] = "success"
                                return facts['ansible_facts']
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error in ansible output for {target}: {e}")
                            continue
            logger.warning(f"No valid facts JSON found in ansible output for {target}")
            return None
        except Exception as e:
            logger.error(f"Error parsing ansible output for {target}: {e}")
            return None

    def _create_fallback_facts(self, target: str) -> Dict[str, Any]:
        return {
            "ansible_hostname": "unknown",
            "ansible_default_ipv4": {"address": target},
            "ansible_distribution": "Unknown",
            "ansible_os_family": "Unknown",
            "ansible_processor_vcpus": 1,
            "ansible_memtotal_mb": 1024,
            "ansible_kernel": "Unknown",
            "discovery_status": "failed",
            "discovery_method": "fallback"
        }