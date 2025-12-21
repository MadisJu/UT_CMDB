import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from datetime import datetime
from pydantic import ValidationError
from src.core.logging_adapter import record_job_run

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
    start_time = datetime.utcnow()
    from src.core.plugins.plugin_loader import get_plugin
    from src.core.models.asset_model import HostAsset
    try:
        logger.info(f"Starting discovery task for host: {host}")
        plugin_instance = get_plugin("ansible")
        result = plugin_instance.discover(host, user)
        if result:
            asset = _coerce_asset_model(result)
            logger.info(f"Discovered asset prepared: {asset.hostname}")
            
            record_job_run(
                job_name="discovery_task",
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="success",
                processed_count=1,
                diagnostics={"hostname": asset.hostname}
            )
            return asset.dict() if asset else result
        else:
            record_job_run(
                job_name="discovery_task",
                start_time=start_time,
                end_time=datetime.utcnow(),
                status="success",
                processed_count=0,
                diagnostics={"message": "No result returned"}
            )
            return None
    except Exception as e:
        logger.error(f"Discovery task failed for {host}: {e}")
        record_job_run(
            job_name="discovery_task",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="failure",
            processed_count=0,
            diagnostics={"error": str(e), "host": host}
        )
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name="worker.tasks.discovery.batch_discovery_task", bind=True, max_retries=3)
def batch_discovery_task(self, hosts, user):
    # discover multiple hosts using Ansible plugin
    start_time = datetime.utcnow()
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
                    f"Jira sync completed: {jira_summary.get('created', 0)} created, "
                    f"{jira_summary.get('updated', 0)} updated"
                )
        except Exception as e:
            logger.error(f"Failed to sync batch results to Jira: {e}")
            jira_summary = {"error": str(e)}

        record_job_run(
            job_name="batch_discovery_task",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="success",
            processed_count=len(assets),
            diagnostics={
                "hosts_count": len(hosts),
                "jira_sync": jira_summary
            }
        )
        
        return {
            "status": "success",
            "discovered_count": len(assets),
            "assets": assets,
            "jira_sync": jira_summary
        }

    except Exception as exc:
        logger.error(f"Batch discovery task failed: {exc}", exc_info=True)
        record_job_run(
            job_name="batch_discovery_task",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="failure",
            processed_count=0,
            diagnostics={"error": str(exc)}
        )
        raise self.retry(exc=exc, countdown=60)
