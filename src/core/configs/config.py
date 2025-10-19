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

    # --- Redis / Celery ---
    redis_url: str = Field("redis://localhost:6379/0", description="Redis broker URL for Celery")
    celery_result_backend: str = Field("redis://localhost:6379/1", description="Redis backend for Celery results")

    # --- Jira ---
    jira_url: Optional[str] = Field(None, description="Jira base URL, e.g. https://yourcompany.atlassian.net")
    jira_api_token: Optional[str] = Field(None, description="Jira API token")
    jira_user_email: Optional[str] = Field(None, description="Email of API user")
    jira_asset_workspace_id: Optional[str] = Field(None, description="ID of the Jira Assets workspace")
    jira_cloud_id: Optional[str] = Field(None, description="Jira Cloud ID")

    # --- CMDB ---
    cmdb_host: Optional[str] = Field(None, description="CMDB host IP address")
    cmdb_user: Optional[str] = Field(None, description="CMDB user")
    cmdb_interval_seconds: Optional[int] = Field(None, description="CMDB discovery interval in seconds")

    # --- Ansible ---
    ansible_inventory_path: str = Field("inventories/default_inventory.ini")
    ansible_playbook_path: str = Field("playbooks/discovery.yml")
    ansible_timeout: int = 300

    address_book_path: Path = Field(default=Path(__file__).parent.parent / "config" / "config.json",
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

    class Config:
        env_file = ".env"  # load from .env file if present

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
