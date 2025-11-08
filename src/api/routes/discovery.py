from fastapi import APIRouter, status, Depends, HTTPException, Body
from pydantic import BaseModel
import uuid
from typing import Optional
from src.core.plugins.ansible_plugin import AnsiblePlugin
from src.core.models.fact_parser import parse_ansible_facts, parse_linux_facts, parse_windows_facts, parse_sparc_facts
from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from src.worker.tasks.discovery import discovery_task, batch_discovery_task
from src.worker.tasks.auto_discovery import auto_discovery_task, discovery_by_type_task
from src.core.services.machine_inventory import MachineInventory
from src.worker.tasks.sync_to_jira import sync_discovered_assets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Discovery"]
)

# Dependency to get Ansible plugin
def get_ansible_plugin():
    return AnsiblePlugin()

# Dependency to get machine inventory
def get_machine_inventory():
    return MachineInventory()

class DiscoveryRequest(BaseModel):
    target_host: Optional[str] = None
    user: Optional[str] = None


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def start_discovery_job(
    payload: DiscoveryRequest = Body(...),
    ansible_plugin: AnsiblePlugin = Depends(get_ansible_plugin)
):
    """
    Start a new asset discovery job.

    This is a long-running operation that runs in the background.
    API returns immediately with a job ID to track the status.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Resolve target_host and user from request body with env fallbacks
        import os
        target_host = payload.target_host or os.getenv("CMDB_HOST", "25.44.45.59")
        user = payload.user or os.getenv("CMDB_USER", "chronia")

        # Start Celery task for discovery
        task = discovery_task.delay(target_host, user)
        
        logger.info(f"Started discovery job {job_id} for host {target_host}")
        
        return {
            "message": "Asset discovery job has been started.", 
            "job_id": job_id,
            "task_id": task.id,
            "target_host": target_host,
            "user": user
        }
        
    except Exception as e:
        logger.error(f"Failed to start discovery job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery job: {str(e)}"
        )

@router.post("/auto", status_code=status.HTTP_202_ACCEPTED)
def start_auto_discovery_job(
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """
    Start automatic discovery of all configured machines and sync to Jira.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Chain the tasks: auto_discovery_task -> sync_discovered_assets
        task_chain = (auto_discovery_task.s() | sync_discovered_assets.s())
        task = task_chain.apply_async()
        
        logger.info(f"Started auto discovery and sync job {job_id}")
        
        return {
            "message": "Auto discovery and Jira sync job has been started.", 
            "job_id": job_id,
            "task_id": task.id,
            "target_machines": len(inventory.get_enabled_machines())
        }
        
    except Exception as e:
        logger.error(f"Failed to start auto discovery job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start auto discovery job: {str(e)}"
        )

@router.post("/type/{machine_type}", status_code=status.HTTP_202_ACCEPTED)
def start_type_discovery_job(
    machine_type: str,
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """
    Start discovery for machines of a specific type.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Start Celery task for type discovery
        task = discovery_by_type_task.delay(machine_type)
        
        logger.info(f"Started {machine_type} discovery job {job_id}")
        
        return {
            "message": f"{machine_type.title()} discovery job has been started.", 
            "job_id": job_id,
            "task_id": task.id,
            "machine_type": machine_type,
            "target_machines": len(inventory.get_machines_by_type(machine_type))
        }
        
    except Exception as e:
        logger.error(f"Failed to start {machine_type} discovery job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start {machine_type} discovery job: {str(e)}"
        )

@router.post("/immediate", status_code=status.HTTP_200_OK)
def discover_immediate(
    target_host: str,
    user: Optional[str] = None,
    ansible_plugin: AnsiblePlugin = Depends(get_ansible_plugin)
):
    """
    Perform immediate asset discovery for a specific host.
    
    This runs synchronously and returns the discovered asset data.
    """
    try:
        # Use Ansible plugin to discover the host
        facts = ansible_plugin.discover(target_host, user)
        
        # Parse facts into appropriate asset model
        if facts.get("os", "").lower() in ["linux", "ubuntu", "centos", "rhel", "debian"]:
            asset = parse_linux_facts(facts)
        elif facts.get("os", "").lower() in ["windows"]:
            asset = parse_windows_facts(facts)
        elif facts.get("os", "").lower() in ["solaris"]:
            asset = parse_sparc_facts(facts)
        else:
            asset = parse_ansible_facts(facts)
        
        logger.info(f"Discovered asset: {asset.hostname}")
        
        return {
            "message": "Asset discovery completed successfully",
            "asset": asset.dict(),
            "target_host": target_host
        }
        
    except Exception as e:
        logger.error(f"Failed to discover asset for {target_host}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover asset: {str(e)}"
        )