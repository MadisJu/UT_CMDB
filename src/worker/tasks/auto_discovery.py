"""
Automatic discovery task for all configured machines.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.services.machine_inventory import MachineInventory
from src.core.plugins.ansible_plugin import AnsiblePlugin
from src.core.models.fact_parser import parse_facts_to_asset
from src.core.models.asset_model import HostAsset

logger = logging.getLogger(__name__)


@celery_app.task(name="src.worker.tasks.auto_discovery.auto_discovery_task", bind=True, max_retries=3)
def auto_discovery_task(self):
    """
    Celery task for automatic discovery of all configured machines.
    
    Returns:
        Dictionary containing discovered assets information
    """
    try:
        logger.info("Starting automatic discovery task")
        
        # Initialize machine inventory
        inventory = MachineInventory()
        
        # Get all enabled machines
        machines = inventory.get_enabled_machines()
        
        if not machines:
            logger.warning("No enabled machines found in inventory")
            return {
                "status": "success",
                "message": "No machines to discover",
                "discovered_count": 0,
                "assets": []
            }
        
        logger.info(f"Found {len(machines)} enabled machines for discovery")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(machines), 'status': f'Starting discovery of {len(machines)} machines...'}
        )
        
        # Get discovery settings
        discovery_settings = inventory.get_discovery_settings()
        default_user = discovery_settings.get("default_user", "root")
        
        # Initialize Ansible plugin
        ansible_plugin = AnsiblePlugin()
        
        # Discover all machines
        discovered_assets = []
        failed_discoveries = []
        
        for i, machine in enumerate(machines):
            try:
                host = machine.get("ip_address") or machine.get("hostname")
                user = machine.get("user") or default_user
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(machines), 
                        'status': f'Discovering {host} ({i+1}/{len(machines)})...'
                    }
                )
                
                logger.info(f"Discovering machine: {host}")
                
                # Discover the machine
                facts = ansible_plugin.discover(host, user)
                
                # Facts is already a parsed asset, convert to dict if needed
                if isinstance(facts, dict):
                    asset_dict = facts
                else:
                    asset_dict = facts.dict()
                
                # Add machine configuration metadata
                if "metadata" not in asset_dict:
                    asset_dict["metadata"] = {}
                asset_dict["metadata"].update({
                    "configured_type": machine.get("type"),
                    "description": machine.get("description"),
                    "discovery_method": "auto_discovery",
                    "source_config": "machine_inventory"
                })
                
                discovered_assets.append(asset_dict)
                logger.info(f"Successfully discovered {host}: {asset_dict.get('hostname', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Failed to discover machine {machine.get('hostname', 'unknown')}: {e}")
                
                # Create fallback asset
                fallback_asset = HostAsset(
                    name=machine.get("hostname", "unknown"),
                    type=machine.get("type", "unknown"),
                    hostname=machine.get("hostname", "unknown"),
                    ip_address=machine.get("ip_address", "unknown"),
                    os="Unknown",
                    cpu_cores=0,
                    memory_mb=0,
                    metadata={
                        "source": "auto_discovery_fallback",
                        "error": str(e),
                        "configured_type": machine.get("type"),
                        "description": machine.get("description")
                    }
                )
                discovered_assets.append(fallback_asset.dict())
                failed_discoveries.append({
                    "host": machine.get("hostname", "unknown"),
                    "error": str(e)
                })
        
        # Update final state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': len(machines), 
                'total': len(machines), 
                'status': f'Completed discovery of {len(machines)} machines'
            }
        )
        
        logger.info(f"Auto discovery completed: {len(discovered_assets)} assets discovered, {len(failed_discoveries)} failures")
        
        # Return results
        return {
            "status": "success",
            "message": f"Auto discovery completed for {len(machines)} machines",
            "discovered_count": len(discovered_assets),
            "failed_count": len(failed_discoveries),
            "assets": discovered_assets,
            "failed_discoveries": failed_discoveries,
            "discovery_method": "auto_discovery",
            "inventory_summary": inventory.get_inventory_summary()
        }
    
    except Exception as exc:
        logger.error(f"Auto discovery task failed: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': 1, 'status': f'Auto discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="src.worker.tasks.auto_discovery.discovery_by_type_task", max_retries=3, bind=True)
def discovery_by_type_task(self, machine_type: str):
    """
    Celery task for discovering machines of a specific type.
    
    Args:
        self: The Celery task instance.
        machine_type: Type of machines to discover (e.g., 'linux', 'windows')
        
    Returns:
        Dictionary containing discovered assets information
    """
    try:
        logger.info(f"Starting discovery task for {machine_type} machines")
        
        # Initialize machine inventory
        inventory = MachineInventory()
        
        # Get machines of specified type
        machines = inventory.get_machines_by_type(machine_type)
        
        if not machines:
            logger.warning(f"No {machine_type} machines found in inventory")
            return {
                "status": "success",
                "message": f"No {machine_type} machines to discover",
                "discovered_count": 0,
                "assets": []
            }
        
        logger.info(f"Found {len(machines)} {machine_type} machines for discovery")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(machines), 'status': f'Starting discovery of {len(machines)} {machine_type} machines...'}
        )
        
        # Get discovery settings
        discovery_settings = inventory.get_discovery_settings()
        default_user = discovery_settings.get("default_user", "root")
        
        # Initialize Ansible plugin
        ansible_plugin = AnsiblePlugin()
        
        # Discover machines
        discovered_assets = []
        failed_discoveries = []
        
        for i, machine in enumerate(machines):
            try:
                host = machine.get("ip_address") or machine.get("hostname")
                user = machine.get("user") or default_user
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(machines), 
                        'status': f'Discovering {host} ({i+1}/{len(machines)})...'
                    }
                )
                
                logger.info(f"Discovering {machine_type} machine: {host}")
                
                # Discover the machine
                facts = ansible_plugin.discover(host, user)
                
                # Parse facts into asset model
                asset = parse_facts_to_asset(facts)
                
                # Add machine configuration metadata
                if asset.metadata is None:
                    asset.metadata = {}
                asset.metadata.update({
                    "configured_type": machine.get("type"),
                    "description": machine.get("description"),
                    "discovery_method": "type_discovery",
                    "source_config": "machine_inventory"
                })
                
                discovered_assets.append(asset.dict())
                logger.info(f"Successfully discovered {host}: {asset.hostname}")
                
            except Exception as e:
                logger.error(f"Failed to discover {machine_type} machine {machine.get('hostname', 'unknown')}: {e}")
                
                # Create fallback asset
                fallback_asset = HostAsset(
                    name=machine.get("hostname", "unknown"),
                    type=machine.get("type", "unknown"),
                    hostname=machine.get("hostname", "unknown"),
                    ip_address=machine.get("ip_address", "unknown"),
                    os="Unknown",
                    cpu_cores=0,
                    memory_mb=0,
                    metadata={
                        "source": "type_discovery_fallback",
                        "error": str(e),
                        "configured_type": machine.get("type"),
                        "description": machine.get("description")
                    }
                )
                discovered_assets.append(fallback_asset.dict())
                failed_discoveries.append({
                    "host": machine.get("hostname", "unknown"),
                    "error": str(e)
                })
        
        # Update final state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': len(machines), 
                'total': len(machines), 
                'status': f'Completed discovery of {len(machines)} {machine_type} machines'
            }
        )
        
        logger.info(f"Type discovery completed: {len(discovered_assets)} {machine_type} assets discovered, {len(failed_discoveries)} failures")
        
        # Return results
        return {
            "status": "success",
            "message": f"Type discovery completed for {len(machines)} {machine_type} machines",
            "machine_type": machine_type,
            "discovered_count": len(discovered_assets),
            "failed_count": len(failed_discoveries),
            "assets": discovered_assets,
            "failed_discoveries": failed_discoveries,
            "discovery_method": "type_discovery"
        }
    
    except Exception as exc:
        logger.error(f"Type discovery task failed: {exc}")
        
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': 1, 'status': f'Type discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)
