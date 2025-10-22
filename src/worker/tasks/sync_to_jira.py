import logging
import sys
from pathlib import Path
from celery.utils.log import get_task_logger

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.integrations.jira_client import JiraClient

logger = get_task_logger(__name__)

@celery_app.task(name="worker.tasks.sync_to_jira.sync_discovered_assets", bind=True, max_retries=3)
def sync_discovered_assets(self, discovery_result: dict):
    """
    Celery task for syncing discovered assets to Jira.
    This task receives the result from a discovery task, extracts the list of assets,
    and passes them to the Jira client for synchronization.

    Args:
        self: The task instance.
        discovery_result (dict): A dictionary containing the results of the discovery task.
                                 It is expected to have an 'assets' key with a list of
                                 asset model objects (e.g., HostAsset).

    Returns:
        dict: A dictionary containing the results of the sync operation.
    """
    logger.info("Starting sync of discovered assets to Jira.")
    logger.debug(f"Received discovery result: {discovery_result}")

    # The discovery task returns a dictionary, e.g., {'assets': [<HostAsset object>]}.
    # We need to extract the list of asset objects from it.
    assets_to_sync = discovery_result.get('assets', [])

    if not assets_to_sync:
        logger.warning("No assets found in the discovery result to sync.")
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
        
        return {
            "status": "success",
            "synced_items": len(assets_to_sync),
            "results": sync_results
        }

    except Exception as exc:
        logger.error(f"Sync of discovered assets failed: {exc}", exc_info=True)
        self.update_state(
            state='FAILURE',
            meta={'status': f'Sync failed: {str(exc)}'}
        )
        raise self.retry(exc=exc, countdown=60)
