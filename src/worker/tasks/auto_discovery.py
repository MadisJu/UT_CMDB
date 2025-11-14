import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.configs.celery_config import celery_app
from src.core.services.machine_inventory import MachineInventory
from src.core.plugins.ansible_plugin import AnsiblePlugin
from src.core.models.fact_parser import parse_facts_to_asset
from src.core.models.asset_model import HostAsset
from src.worker.tasks.sync_to_jira import sync_discovered_assets


logger = logging.getLogger(__name__)


@celery_app.task(name="src.worker.tasks.auto_discovery.auto_discovery_and_sync")
def auto_discovery_and_sync_task():
    (auto_discovery_task.s() | sync_discovered_assets.s()).apply_async()

@celery_app.task(name="src.worker.tasks.auto_discovery.auto_discovery_task", bind=True, max_retries=3)
def auto_discovery_task(self):
    try:
        logger.info("Starting automatic discovery task")
        
        inventory = MachineInventory()
        
        machines = inventory.get_target_hosts_with_users()
        
        if not machines:
            logger.warning("No enabled machines found in inventory")
            return {
                "status": "success",
                "message": "No machines to discover",
                "discovered_count": 0,
                "assets": []
            }
        
        logger.info(f"Found {len(machines)} enabled machines for discovery")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(machines), 'status': f'Starting discovery of {len(machines)} machines...'}
        )
        
        ansible_plugin = AnsiblePlugin()
        
        discovered_assets = []
        failed_discoveries = []
        
        logger.info(machines)

        for i, (host_name, user) in enumerate(machines):


            host_vars = inventory.get_host_vars(host_name)

            logger.info(host_vars)

            host = host_vars.get("ansible_host", host_name)  # Use IP if defined
            user = host_vars.get("ansible_user", user) 

            try:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(machines), 
                        'status': f'Discovering {host} ({i+1}/{len(machines)})...'
                    }
                )
                
                logger.info(f"Discovering machine: {host}")
                
                is_windows = (
                    host_vars.get("type") == "windows" or
                    host_vars.get("ansible_winrm_transport") == "basic"
                )

                if(is_windows):
                    facts = ansible_plugin.discover(host, user, is_windows, host_vars.get("ansible_password"))
                else:
                    facts = ansible_plugin.discover(host, user)   
                
                asset = parse_facts_to_asset(facts)
                
                host_vars = inventory.get_host_vars(host)
                
                discovered_assets.append(asset.dict())
                logger.info(f"Successfully discovered {host}: {asset.hostname}")
                
            except Exception as e:
                logger.error(f"Failed to discover machine {host}: {e}")
                
                fallback_asset = HostAsset(
                    type=host_vars.get("type", "unknown"),
                    hostname=host,
                    ip_address=host,
                    os="Unknown",
                    cpu_cores=0,
                    memory_mb=0,
                )
                discovered_assets.append(fallback_asset.dict())
                failed_discoveries.append({
                    "host": host,
                    "error": str(e)
                })
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': len(machines), 
                'total': len(machines), 
                'status': f'Completed discovery of {len(machines)} machines'
            }
        )
        
        logger.info(f"Auto discovery completed: {len(discovered_assets)} assets discovered, {len(failed_discoveries)} failures")
        
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
        
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': 1, 'status': f'Auto discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="src.worker.tasks.auto_discovery.discovery_by_type_task", max_retries=3, bind=True)
def discovery_by_type_task(self, machine_type: str):

    try:
        logger.info(f"Starting discovery task for {machine_type} machines")
        
        inventory = MachineInventory()
        
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
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': len(machines), 'status': f'Starting discovery of {len(machines)} {machine_type} machines...'}
        )
        
        ansible_plugin = AnsiblePlugin()
        
        discovered_assets = []
        failed_discoveries = []
        
        for i, machine in enumerate(machines):
            try:
                host = machine.get("ip_address") or machine.get("hostname")
                user = machine.get("user") or "root"
                
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': i, 
                        'total': len(machines), 
                        'status': f'Discovering {host} ({i+1}/{len(machines)})...'
                    }
                )
                
                logger.info(f"Discovering {machine_type} machine: {host}")
                
                facts = ansible_plugin.discover(host, user)
                
                asset = parse_facts_to_asset(facts)
                
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
                
                fallback_asset = HostAsset(
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
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': len(machines), 
                'total': len(machines), 
                'status': f'Completed discovery of {len(machines)} {machine_type} machines'
            }
        )
        
        logger.info(f"Type discovery completed: {len(discovered_assets)} {machine_type} assets discovered, {len(failed_discoveries)} failures")
        
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
        
        self.update_state(
            state='FAILURE',
            meta={'current': 0, 'total': 1, 'status': f'Type discovery failed: {str(exc)}'}
        )
        
        raise self.retry(exc=exc, countdown=60)
