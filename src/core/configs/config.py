import json
import logging
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


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
    ansible_inventory_path: Path = Field(
        default=Path(__file__).resolve().parent / "inventory.ini",
        description="Path to the Ansible inventory ini file",
    )
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

    def get_ansible_inventory(self) -> Dict[str, Any]:
        """Load and normalize Ansible inventory data."""
        path = self._resolve_inventory_path()
        raw_inventory = self._load_inventory_with_fallback(path)
        return self._normalize_inventory(raw_inventory)

    def _resolve_inventory_path(self) -> Path:
        path = Path(self.ansible_inventory_path).expanduser()

        if not path.is_absolute():
            candidate = (Path(__file__).resolve().parent / path).resolve()
            if candidate.exists():
                path = candidate
            else:
                path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"Ansible inventory is not found at {path}")

        return path

    def _load_inventory_with_fallback(self, path: Path) -> Dict[str, Any]:
        """
        Try to load the inventory using the Ansible CLI.
        If that fails (e.g. ansible not installed), fall back to parsing the ini file directly.
        """
        try:
            return self._load_inventory_with_cli(path)
        except Exception as cli_error:
            logger.warning(
                "Failed to load inventory with ansible-inventory, falling back to ini parser: %s",
                cli_error,
            )
            return self._parse_inventory_file(path)

    def _load_inventory_with_cli(self, path: Path) -> Dict[str, Any]:
        process = subprocess.run(
            ["ansible-inventory", "--list", "-i", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return json.loads(process.stdout)

    def _parse_inventory_file(self, path: Path) -> Dict[str, Any]:
        """Minimal parser for ini-style Ansible inventories."""
        groups: Dict[str, Dict[str, Any]] = {}
        hostvars: Dict[str, Dict[str, Any]] = {}

        current_group = "ungrouped"
        section_modifier: Optional[str] = None
        groups[current_group] = {"hosts": [], "children": [], "vars": {}}

        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", ";")):
                continue

            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                if ":" in section:
                    group_name, modifier = section.split(":", 1)
                    current_group = group_name.strip()
                    section_modifier = modifier.strip()
                else:
                    current_group = section
                    section_modifier = None

                groups.setdefault(current_group, {"hosts": [], "children": [], "vars": {}})
                continue

            if section_modifier == "vars":
                key, _, value = line.partition("=")
                if key:
                    groups[current_group]["vars"][key.strip()] = value.strip()
                continue

            if section_modifier == "children":
                child = line.strip()
                if child:
                    groups[current_group].setdefault("children", []).append(child)
                continue

            parts = shlex.split(line)
            if not parts:
                continue

            host = parts[0]
            groups[current_group].setdefault("hosts", []).append(host)

            vars_for_host = {}
            for token in parts[1:]:
                if "=" in token:
                    key, value = token.split("=", 1)
                    vars_for_host[key.strip()] = value.strip()

            hostvars[host] = {**hostvars.get(host, {}), **vars_for_host}

        if "all" not in groups:
            groups["all"] = {"hosts": [], "children": [], "vars": {}}

        groups["all"].setdefault("children", [])
        for group_name in groups.keys():
            if group_name != "all" and group_name not in groups["all"]["children"]:
                groups["all"]["children"].append(group_name)

        return {"_meta": {"hostvars": hostvars}, **groups}

    def _normalize_inventory(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize inventory to unified structure with hostvars on every group."""
        hostvars = raw.get("_meta", {}).get("hostvars", {})

        groups = {
            name: data
            for name, data in raw.items()
            if name != "_meta" and isinstance(data, dict)
        }

        def resolve_hosts(group_name: str, visited=None) -> list:
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
