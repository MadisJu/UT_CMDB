import json
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.plugins.ansible_plugin import AnsiblePlugin
from src.core.models.fact_parser import parse_facts_to_asset
from src.core.models.asset_model import HostAsset

logger = logging.getLogger(__name__)

# Task for getting data from Ansible

@celery_app.task(name="worker.tasks.discovery.discovery_task", max_retries=3)
def discovery_task(host, user):
    """
    Celery task for discovering host facts using Ansible.
    
    Args:
        host: Target host IP or hostname
        user: SSH user for connection
        
    Returns:
        Dictionary containing discovered asset information
    """
    try:
        logger.info(f"Starting discovery task for host: {host}")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 1, 'status': f'Discovering {host}...'}
        )
        
        # Use Ansible plugin for discovery
        ansible_plugin = AnsiblePlugin()
        facts = ansible_plugin.discover(host, user)
        
        # Parse facts into asset model
        asset = parse_facts_to_asset(facts)
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 1, 'status': f'Successfully discovered {host}'}
        )
        
        logger.info(f"Successfully discovered {host}: {asset.hostname}")
        
        # Return asset data
        return {
            "status": "success",
            "host": host,
            "asset": asset.dict(),
            "discovery_method": "ansible",
            "facts_count": len(facts)
        }
    
    except Exception as exc:
        logger.error(f"Discovery task failed for {host}: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 1, 'total': 1, 'status': f'Discovery failed for {host}: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="worker.tasks.discovery.batch_discovery_task", max_retries=3)
def batch_discovery_task(hosts, user):
    """
    Celery task for discovering multiple hosts using Ansible.
    
    Args:
        hosts: List of target host IPs or hostnames
        user: SSH user for connection
        
    Returns:
        Dictionary containing discovered assets information
    """
    try:
        logger.info(f"Starting batch discovery task for {len(hosts)} hosts")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(hosts), 'status': f'Starting batch discovery for {len(hosts)} hosts...'}
        )
        
        # Use Ansible plugin for batch discovery
        ansible_plugin = AnsiblePlugin()
        facts_dict = ansible_plugin.discover_all(hosts, user)
        
        # Parse facts into asset models
        assets = []
        for host, facts in facts_dict.items():
            try:
                asset = parse_facts_to_asset(facts)
                assets.append(asset.dict())
                
                # Update progress
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
                # Create fallback asset
                fallback_asset = HostAsset(
                    name=host,
                    hostname=host,
                    ip_address=host,
                    os="Unknown",
                    metadata={"source": "ansible_fallback", "error": str(e)}
                )
                assets.append(fallback_asset.dict())
        
        logger.info(f"Successfully completed batch discovery for {len(hosts)} hosts")
        
        # Return results
        return {
            "status": "success",
            "hosts": hosts,
            "assets": assets,
            "discovery_method": "ansible_batch",
            "total_discovered": len(assets)
        }
    
    except Exception as exc:
        logger.error(f"Batch discovery task failed: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': len(hosts), 'status': f'Batch discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)