from src.core.plugins.base_plugin import BasePlugin
from src.core.configs import config
import ansible_runner
from pathlib import Path


class AnsiblePlugin(BasePlugin):
    name = "ansible"
    description = "Fetches host facts via Ansible"

    def discover(self, target: str):
        # TURN ANSIBLE OVER HERE OR SOMETHING IDK
        return {"hostname": target, "os": "Linux", "ip": "10.0.0.5"}