"""
Machine inventory management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from src.core.services.machine_inventory import MachineInventory
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inventory",
    tags=["Machine Inventory"]
)

# Dependency to get machine inventory service
def get_machine_inventory():
    return MachineInventory()

@router.get("/machines", response_model=List[Dict[str, Any]])
def get_all_machines(inventory: MachineInventory = Depends(get_machine_inventory)):
    """Get all configured machines."""
    try:
        return inventory.get_all_machines()
    except Exception as e:
        logger.error(f"Failed to get machines: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get machines: {str(e)}"
        )

@router.get("/machines/enabled", response_model=List[Dict[str, Any]])
def get_enabled_machines(inventory: MachineInventory = Depends(get_machine_inventory)):
    """Get only enabled machines."""
    try:
        return inventory.get_enabled_machines()
    except Exception as e:
        logger.error(f"Failed to get enabled machines: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enabled machines: {str(e)}"
        )

@router.get("/machines/type/{machine_type}", response_model=List[Dict[str, Any]])
def get_machines_by_type(
    machine_type: str,
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """Get machines by type."""
    try:
        return inventory.get_machines_by_type(machine_type)
    except Exception as e:
        logger.error(f"Failed to get {machine_type} machines: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get {machine_type} machines: {str(e)}"
        )

@router.get("/machines/hostname/{hostname}", response_model=Dict[str, Any])
def get_machine_by_hostname(
    hostname: str,
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """Get machine by hostname or IP."""
    try:
        machine = inventory.get_machine_by_hostname(hostname)
        if not machine:
            raise HTTPException(
                status_code=404,
                detail=f"Machine not found: {hostname}"
            )
        return machine
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get machine {hostname}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get machine: {str(e)}"
        )

@router.get("/summary", response_model=Dict[str, Any])
def get_inventory_summary(inventory: MachineInventory = Depends(get_machine_inventory)):
    """Get inventory summary."""
    try:
        return inventory.get_inventory_summary()
    except Exception as e:
        logger.error(f"Failed to get inventory summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get inventory summary: {str(e)}"
        )

@router.post("/machines", status_code=status.HTTP_201_CREATED)
def add_machine(
    machine_config: Dict[str, Any],
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """Add a new machine to the inventory."""
    try:
        success = inventory.add_machine(machine_config)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to add machine - check required fields"
            )
        return {"message": "Machine added successfully", "machine": machine_config}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add machine: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add machine: {str(e)}"
        )

@router.put("/machines/{hostname}", status_code=status.HTTP_200_OK)
def update_machine(
    hostname: str,
    updates: Dict[str, Any],
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """Update a machine configuration."""
    try:
        success = inventory.update_machine(hostname, updates)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Machine not found: {hostname}"
            )
        return {"message": f"Machine {hostname} updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update machine {hostname}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update machine: {str(e)}"
        )

@router.delete("/machines/{hostname}", status_code=status.HTTP_200_OK)
def remove_machine(
    hostname: str,
    inventory: MachineInventory = Depends(get_machine_inventory)
):
    """Remove a machine from the inventory."""
    try:
        success = inventory.remove_machine(hostname)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Machine not found: {hostname}"
            )
        return {"message": f"Machine {hostname} removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove machine {hostname}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove machine: {str(e)}"
        )

@router.get("/targets", response_model=List[str])
def get_target_hosts(inventory: MachineInventory = Depends(get_machine_inventory)):
    """Get list of target host IPs/hostnames for discovery."""
    try:
        return inventory.get_target_hosts()
    except Exception as e:
        logger.error(f"Failed to get target hosts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get target hosts: {str(e)}"
        )

@router.get("/targets/with-users", response_model=List[List[str]])
def get_target_hosts_with_users(inventory: MachineInventory = Depends(get_machine_inventory)):
    """Get list of (host, user) tuples for discovery."""
    try:
        targets = inventory.get_target_hosts_with_users()
        # Convert tuples to lists for JSON serialization
        return [[host, user] for host, user in targets]
    except Exception as e:
        logger.error(f"Failed to get target hosts with users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get target hosts with users: {str(e)}"
        )
