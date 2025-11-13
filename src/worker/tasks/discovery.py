import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from pydantic import ValidationError

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.core.configs.celery_config import celery_app
from celery.exceptions import Ignore

logger = logging.getLogger(__name__)

_ASSET_MODELS: Iterable[type[HostAsset]] = (
    LinuxAsset,
    WindowsAsset,
    SparcAsset,
    HostAsset,
)


def _looks_like_raw_facts(payload: Dict[str, Any]) -> bool:
    return any(key.startswith("ansible_") for key in payload)


def _coerce_asset_model(payload: Dict[str, Any]) -> HostAsset:
    from src.core.models.fact_parser import parse_facts_to_asset
    from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
    normalised = dict(payload)
    normalised.setdefault("type", "host")
    normalised.setdefault("source", "ansible")
    normalised.setdefault("metadata", {})

    if _looks_like_raw_facts(normalised):
        return parse_facts_to_asset(normalised)

    for model_cls in _ASSET_MODELS:
        try:
            return model_cls.model_validate(normalised) 
        except ValidationError:
            continue

    hostname = normalised.get("hostname") or normalised.get("name") or "unknown"

    return HostAsset(
        type=normalised.get("type", "host"),
        source=normalised.get("source", "ansible"),
        metadata=normalised.get("metadata", {}),
        hostname=hostname,
        ip_address=normalised.get("ip_address"),
        os=normalised.get("os"),
        cpu_cores=normalised.get("cpu_cores"),
        memory_mb=normalised.get("memory_mb"),
        tags=normalised.get("tags", []),
    )

# Task for getting data from Ansible

@celery_app.task(bind=True, max_retries=3)
def discovery_task(self, host: str, user: str):
    """
    Task to discover a single host.
    """
    from src.core.plugins.plugin_loader import get_plugin
    from src.core.models.asset_model import HostAsset
    try:
        logger.info(f"Starting discovery task for host: {host}")
        plugin_instance = get_plugin("ansible")
        result = plugin_instance.discover(host, user)
        if result:
            asset = _coerce_asset_model(result)
            logger.info(f"Discovered asset prepared: {asset.hostname}")
        return asset.dict() if asset else result
    except Exception as e:
        logger.error(f"Discovery task failed for {host}: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="worker.tasks.discovery.batch_discovery_task", bind=True, max_retries=3)
def batch_discovery_task(self, hosts, user):
    # discover multiple hosts using Ansible plugin
    from src.core.plugins.ansible_plugin import AnsiblePlugin
    from src.core.models.asset_model import HostAsset
    from src.core.services.jira_service import JiraService
    try:
        logger.info(f"Starting batch discovery task for {len(hosts)} hosts")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(hosts), 'status': f'Starting batch discovery for {len(hosts)} hosts...'}
        )
        
        ansible_plugin = AnsiblePlugin()
        facts_dict = ansible_plugin.discover_all(hosts, user)
        
        assets = []
        asset_models = []
        for host, facts in facts_dict.items():
            try:
                asset = _coerce_asset_model(facts)
                asset_models.append(asset)
                assets.append(asset.dict())

                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': len(assets), 
                        'total': len(hosts), 
                        'status': f'Discovered {len(assets)}/{len(hosts)} hosts'
                    }
                )
                
            except Exception as e:
                logger.error(f"Failed to parse facts for {host}: {e}")
                fallback_asset = HostAsset(
                    type="host",
                    source="ansible",
                    hostname=host,
                    ip_address=host,
                    os="Unknown",
                    metadata={"source": "ansible_fallback", "error": str(e)}
                )
                assets.append(fallback_asset.dict())
        
        logger.info(f"Successfully completed batch discovery for {len(hosts)} hosts")

        jira_summary: Optional[Dict[str, Any]] = None

        try:
            if asset_models:
                jira_service = JiraService()
                jira_summary = jira_service.sync_assets_from_models(asset_models)
                logger.info(
                    "Jira sync summary - created: %s, updated: %s, errors: %s",
                    jira_summary.get("created"),
                    jira_summary.get("updated"),
                    jira_summary.get("errors"),
                )
        except ValueError as config_error:
            logger.info("Skipping Jira sync: %s", config_error)
            jira_summary = {"skipped": True, "detail": str(config_error)}
        except Exception as jira_error:
            logger.error("Failed to sync assets with Jira: %s", jira_error, exc_info=True)
            jira_summary = {"error": str(jira_error)}
        
        return {
            "status": "success",
            "hosts": hosts,
            "assets": assets,
            "discovery_method": "ansible_batch",
            "total_discovered": len(assets),
            "jira_sync": jira_summary,
        }
    
    except Exception as exc:
        logger.error(f"Batch discovery task failed: {exc}")
        
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': len(hosts), 'status': f'Batch discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)
