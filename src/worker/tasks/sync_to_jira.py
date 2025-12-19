import logging
import sys
from pathlib import Path
from datetime import datetime
from celery.utils.log import get_task_logger
from src.core.logging_adapter import record_job_run

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.integrations.jira_client import JiraClient

logger = get_task_logger(__name__)

@celery_app.task(name="worker.tasks.sync_to_jira.sync_discovered_assets", bind=True, max_retries=3)
def sync_discovered_assets(self, discovery_result: dict):
    start_time = datetime.utcnow()
    logger.info("Starting sync of discovered assets to Jira.")
    logger.debug(f"Received discovery result: {discovery_result}")

    assets_to_sync = discovery_result.get('assets', [])

    if not assets_to_sync:
        logger.warning("No assets found in the discovery result to sync.")
        record_job_run(
            job_name="sync_discovered_assets",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="success",
            processed_count=0,
            diagnostics={"message": "No assets to sync"}
        )
        return {"status": "noop", "message": "No assets to sync."}

    logger.info(f"Found {len(assets_to_sync)} asset(s) to sync.")
    self.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': len(assets_to_sync), 'status': 'Initializing Jira sync...'}
    )

    try:
        jira_client = JiraClient()
        sync_results = jira_client.sync_assets(assets_to_sync)

        logger.info("Successfully synced discovered assets to Jira.")
        self.update_state(state='SUCCESS')
        
        record_job_run(
            job_name="sync_discovered_assets",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="success",
            processed_count=len(assets_to_sync),
            diagnostics={"sync_results": sync_results}
        )
        
        return {
            "status": "success",
            "synced_items": len(assets_to_sync),
            "results": sync_results
        }

    except Exception as exc:
        logger.error(f"Sync of discovered assets failed: {exc}", exc_info=True)
        record_job_run(
            job_name="sync_discovered_assets",
            start_time=start_time,
            end_time=datetime.utcnow(),
            status="failure",
            processed_count=0,
            diagnostics={"error": str(exc)}
        )
        self.update_state(
            state='FAILURE',
            meta={'status': f'Sync failed: {str(exc)}'}
        )
        raise self.retry(exc=exc, countdown=60)
