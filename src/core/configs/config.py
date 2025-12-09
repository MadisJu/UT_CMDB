from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional
import subprocess
import json


class Settings(BaseSettings):

    # --- Core System ---
    env: str = Field("development", description="Environment: dev/staging/prod")
    base_dir: Path = Field(default=Path(__file__).parent.parent)

    # --- Database ---
    database_url: str = Field("sqlite:///./cmdb.db", description="Database connection string (SQLAlchemy URL)")

    celery_broker_url: str = Field("sqlalchemy+sqlite:///celery_broker.db", description="Celery broker URL", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field("db+sqlite:///celery_results.db", description="Celery results backend", alias="CELERY_RESULT_BACKEND")

    # --- Jira ---
    jira_url: Optional[str] = Field(None, description="Jira base URL, e.g. https://yourcompany.atlassian.net")
    jira_api_token: Optional[str] = Field(None, description="Jira API token")
    jira_user_email: Optional[str] = Field(None, description="Email of API user")
    jira_asset_workspace_id: Optional[str] = Field(None, description="ID of the Jira Assets workspace")
    jira_cloud_id: Optional[str] = Field(None, description="Jira Cloud ID")
    jira_proxy_url: Optional[str] = Field(
        None, description="Proxy URL for Jira calls, e.g. http://proxy:3128"
    )
    jira_proxy_username: Optional[str] = Field(
        None, description="Optional username for proxy authentication"
    )
    jira_proxy_password: Optional[str] = Field(
        None, description="Optional password for proxy authentication"
    )

    # --- CMDB ---
    cmdb_host: Optional[str] = Field(None, description="CMDB host IP address")
    cmdb_user: Optional[str] = Field(None, description="CMDB user")
    cmdb_interval_seconds: Optional[int] = Field(None, description="CMDB discovery interval in seconds")

    # --- Ansible ---
    ansible_inventory_path: str = Field("inventories/default_inventory.ini")
    ansible_playbook_path: str = Field("playbooks/discovery.yml")
    ansible_timeout: int = 300
    ansible_user: str = Field("root", description="Default SSH user for Ansible discovery")
    ansible_winrm_port: int = 5985
    ansible_winrm_scheme: str = Field("http", description="WinRM scheme: http or https")
    ansible_winrm_transport: str = Field("basic", description="WinRM transport, e.g. basic or ntlm")
    ansible_winrm_message_encryption: str = Field(
        "auto", description="WinRM message encryption strategy"
    )
    ansible_winrm_server_cert_validation: str = Field(
        "ignore", description="WinRM cert validation policy"
    )
    
    address_book_path: Path = Field(default=Path(__file__).parent / "config.json",
                                    description="Config file path")

    # --- Scheduler ---
    discovery_interval_hours: int = Field(24)
    sync_interval_minutes: int = Field(60)

    # --- Plugins ---
    plugins_dir: Path = Field(default=Path(__file__).parent / "plugins" / "custom")

    # --- Logging ---
    log_level: str = Field("INFO")
    log_dir: Path = Field(default=Path(__file__).parent.parent / "logs")

    # --- Feature Toggles ---
    enable_plugins: bool = True
    enable_jira_sync: bool = True
    enable_ansible_discovery: bool = True

    # --- CMDB Specific ---
    cmdb_host: str = Field("0.0.0.0", description="CMDB API host", alias="CMDB_HOST")
    cmdb_port: int = Field(8000, description="CMDB API port", alias="CMDB_PORT")
    cmdb_user: str = Field("root", description="Default user for discovery", alias="CMDB_USER")
    cmdb_interval_seconds: int = Field(3600, description="Discovery interval in seconds", alias="CMDB_INTERVAL_SECONDS")
    cmdb_debug: bool = Field(False, description="Debug mode", alias="CMDB_DEBUG")

    class Config:
        env_file = Path(__file__).parent / ".env"  
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = "allow" 

    def get_address_book(self) -> list[dict]:
        """Load hosts from the address book JSON."""
        path = self.address_book_path
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("all", [])

    def get_ansible_inventory(self) -> str:
        """Return Ansible inventory path"""

        path = self.ansible_inventory_path

        if not Path(path).exists():
            raise FileNotFoundError(f"Ansible inventory is not found at {path}")

        try:
            process = subprocess.run(
                ["ansible-inventory", "--list", "-i", str(path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            raw = json.loads(process.stdout)

        except Exception as e:
            raise RuntimeError(f"Failed to load Ansible inventory: {e}") from e

        hostvars = raw.get("_meta", {}).get("hostvars", {})

        groups = {
            name: data
            for name, data in raw.items()
            if name != "_meta" and isinstance(data, dict)
        }

        def resolve_hosts(group_name: str, visited=None) -> list:
            """Helper for grouping"""
            if visited is None:
                visited = set()

            if group_name in visited:
                return []

            visited.add(group_name)

            group = groups.get(group_name, {})

            hosts = list(group.get("hosts", []))

            for child in group.get("children", []):
                hosts.extend(resolve_hosts(child, visited))

            seen = set()
            out = []
            for h in hosts:
                if h not in seen:
                    seen.add(h)
                    out.append(h)

            return out

        resolved = {}

        for group_name, group_data in groups.items():

            resolved_hosts = resolve_hosts(group_name)

            resolved[group_name] = {
                "vars": group_data.get("vars", {}),
                "children": group_data.get("children", []),
                "hosts": {
                    host: hostvars.get(host, {})
                    for host in resolved_hosts
                },
            }

        return resolved

        

    def get_discovery_settings(self) -> dict[str, any]:
        """Return discovery_settings dict from config.json (or empty dict)."""
        data = self._load_address_book_json()
        return data.get("discovery_settings", {})

    @property
    def default_discovery_user(self) -> str:
        """
        Resolve default user for discovery: THIS NEEDS TO BE CORRECTED SOON
        """
        ds = self.get_discovery_settings()
        if isinstance(ds, dict) and ds.get("default_user"):
            return ds["default_user"]
        if getattr(self, "ansible_user", None):
            return self.ansible_user
        if getattr(self, "cmdb_user", None):
            return self.cmdb_user
        return "root"
    


settings = Settings()
