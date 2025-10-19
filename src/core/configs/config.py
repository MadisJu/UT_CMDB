from pydantic_settings import BaseSettings
from pydantic import Field, json
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):

    # --- Core System ---
    env: str = Field("development", description="Environment: dev/staging/prod")
    base_dir: Path = Field(default=Path(__file__).parent.parent)

    # --- Database ---
    database_url: str = Field("sqlite:///./cmdb.db", description="Database connection string (SQLAlchemy URL)")

    celery_result_backend: str = Field("db+sqlite:///celery_results.db", description="Celery results backend")

    # --- Jira ---
    jira_url: Optional[str] = Field(None, description="Jira base URL, e.g. https://yourcompany.atlassian.net")
    jira_api_token: Optional[str] = Field(None, description="Jira API token", alias="JIRA_API_TOKEN")
    jira_user_email: Optional[str] = Field(None, description="Email of API user", alias="JIRA_API_USER")
    jira_asset_workspace_id: Optional[str] = Field(None, description="ID of the Jira Assets workspace", alias="JIRA_WORKSPACE_ID")
    jira_cloud_id: Optional[str] = Field(None, description="Jira Cloud ID", alias="JIRA_CLOUD_ID")

    # --- Ansible ---
    ansible_inventory_path: str = Field("inventories/default_inventory.ini")
    ansible_playbook_path: str = Field("playbooks/discovery.yml")
    ansible_timeout: int = 300

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
        env_file = Path(__file__).parent / ".env"  # load from .env file if present
        env_file_encoding = 'utf-8'
        case_sensitive = False

    def get_address_book(self) -> list[dict]:
        """Load hosts from the address book JSON."""
        path = self.address_book_path
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return data.get("all", [])


# Create one global instance
settings = Settings()
