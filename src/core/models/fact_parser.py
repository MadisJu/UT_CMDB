from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def _get_total_disk_gb(facts: Dict[str, Any]) -> float:
    """Calculate total disk size from Ansible facts, focusing on whole physical disks."""
    total_bytes = 0
    try:
        if "ansible_devices" in facts and isinstance(facts["ansible_devices"], dict):
            for device_name, device_info in facts["ansible_devices"].items():
                if device_name[-1].isalpha() and isinstance(device_info, dict) and "size_bytes" in device_info:
                    try:
                        total_bytes += int(device_info["size_bytes"])
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse size_bytes for device {device_name}")

        elif "ansible_mounts" in facts and isinstance(facts["ansible_mounts"], list) and total_bytes == 0:
            seen_devices = set()
            for mount in facts["ansible_mounts"]:
                if isinstance(mount, dict) and "device" in mount and mount["device"].startswith('/dev/'):
                    base_device = ''.join(filter(str.isalpha, mount["device"].split('/')[-1]))
                    if base_device and base_device not in seen_devices:
                        try:
                            total_bytes += int(mount["size_total"])
                            seen_devices.add(base_device)
                        except (ValueError, TypeError):
                             logger.warning(f"Could not parse size_total for mount {mount['device']}")

        elif "ansible_disks" in facts and isinstance(facts["ansible_disks"], list):
            for disk in facts["ansible_disks"]:
                if isinstance(disk, dict) and "size" in disk:
                    try:
                        total_bytes += int(disk["size"])
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse size for a Windows disk.")

        return round(total_bytes / (1024**3), 2) if total_bytes > 0 else 0.0
    
    except Exception as e:
        logger.error(f"An unexpected error occurred in _get_total_disk_gb: {e}")
        return 0.0


def _get_ipv6_address(facts: Dict[str, Any]) -> Optional[str]:
    if "ansible_all_ipv6_addresses" not in facts or not isinstance(facts["ansible_all_ipv6_addresses"], list):
        return None

    addresses = facts["ansible_all_ipv6_addresses"]
    
    for addr_info in addresses:
        if isinstance(addr_info, dict) and addr_info.get("scope") == "global":
            if "temporary" in addr_info and addr_info["temporary"]:
                continue
            return addr_info.get("address")

    for addr_info in addresses:
        address_str = addr_info if isinstance(addr_info, str) else (addr_info.get("address") if isinstance(addr_info, dict) else None)
        if address_str and not address_str.startswith("fe80"):
            return address_str
            
    return None


def _get_processor_type(processor_list: list) -> str:
    # Leiab protsessori tüübi
    if not processor_list or not isinstance(processor_list, list):
        return "N/A"
    
    unique_processors = set(p for p in processor_list if isinstance(p, str) and p)
    
    descriptive_processors = [
        p for p in unique_processors 
        if "intel" in p.lower() or "amd" in p.lower() or "cpu" in p.lower()
    ]
    
    if descriptive_processors:
        return " ".join(sorted(descriptive_processors))
    
    if unique_processors:
        return max(unique_processors, key=len)

    return "N/A"


def parse_ansible_facts(facts: Dict[str, Any]) -> HostAsset:
    """
    Parse Ansible facts into a generic HostAsset.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        HostAsset instance
    """
    try:
        processor_list = facts.get("ansible_processor", [])
        processor_type = _get_processor_type(processor_list)
        
        # Safely get network info
        net_info = facts.get("ansible_default_ipv4", {})
        if not isinstance(net_info, dict):
            net_info = {}

        return HostAsset(
            name=facts.get("ansible_hostname", "unknown"),
            type="host",
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=net_info.get("address", "0.0.0.0"),
            os=facts.get("ansible_distribution", facts.get("ansible_os_family", "Unknown")),
            os_version=facts.get("ansible_distribution_version"),
            model=facts.get("ansible_product_name"),
            mac_address=net_info.get("macaddress"),
            ipv4_address=net_info.get("address"),
            ipv6_address=_get_ipv6_address(facts),
            cpu_cores=facts.get("ansible_processor_cores", 0),
            processor_type=processor_type,
            processor_count=facts.get("ansible_processor_count", 0),
            memory_mb=facts.get("ansible_memtotal_mb", 0),
            swap_total_mb=facts.get("ansible_swaptotal_mb"),
            disk_total_gb=_get_total_disk_gb(facts),
            metadata={"source": "ansible_facts", "discovery_status": "success"}
        )
    except Exception as e:
        logger.error(f"Error parsing Ansible facts: {e}")
        # Return minimal asset on error
        return HostAsset(
            name=facts.get("ansible_hostname", "unknown_error"),
            type="host",
            hostname=facts.get("ansible_hostname", "unknown_error"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address", "0.0.0.0"),
            os="Unknown",
            cpu_cores=0,
            memory_mb=0,
            metadata={"source": "ansible_facts", "error": str(e)}
        )


def parse_linux_facts(facts: Dict[str, Any]) -> LinuxAsset:
    """
    Parse Ansible facts into a LinuxAsset.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        LinuxAsset instance
    """
    try:
        processor_list = facts.get("ansible_processor", [])
        processor_type = _get_processor_type(processor_list)
        
        # Safely get network info
        net_info = facts.get("ansible_default_ipv4", {})
        if not isinstance(net_info, dict):
            net_info = {}
        
        return LinuxAsset(
            name=facts.get("ansible_hostname", "unknown-linux"),
            hostname=facts.get("ansible_hostname", "unknown-linux"),
            ip_address=net_info.get("address", "0.0.0.0"),
            os=facts.get("ansible_distribution", "Linux"),
            os_version=facts.get("ansible_distribution_version"),
            model=facts.get("ansible_product_name"),
            mac_address=net_info.get("macaddress"),
            ipv4_address=net_info.get("address"),
            ipv6_address=_get_ipv6_address(facts),
            cpu_cores=facts.get("ansible_processor_cores", 0),
            processor_type=processor_type,
            processor_count=facts.get("ansible_processor_count", 0),
            memory_mb=facts.get("ansible_memtotal_mb", 0),
            swap_total_mb=facts.get("ansible_swaptotal_mb"),
            disk_total_gb=_get_total_disk_gb(facts),
            distro=facts.get("ansible_distribution"),
            kernel_version=facts.get("ansible_kernel"),
            package_count=len(facts.get("ansible_facts", {}).get("packages", [])),
            metadata={"source": "ansible_linux", "discovery_status": "success"}
        )
    except Exception as e:
        logger.error(f"Error parsing Linux facts: {e}")
        # Return minimal Linux asset on error
        return LinuxAsset(
            name=facts.get("ansible_hostname", "unknown_error"),
            hostname=facts.get("ansible_hostname", "unknown_error"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address", "0.0.0.0"),
            os="Linux",
            cpu_cores=0,
            memory_mb=0,
            metadata={"source": "ansible_linux", "error": str(e)}
        )


def parse_windows_facts(facts: Dict[str, Any]) -> WindowsAsset:
    """
    Parse Ansible facts into a WindowsAsset.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        WindowsAsset instance
    """
    try:
        processor_list = facts.get("ansible_processor", [])
        processor_type = _get_processor_type(processor_list)

        # Safely get network info
        net_info = facts.get("ansible_default_ipv4", {})
        if not isinstance(net_info, dict):
            net_info = {}

        return WindowsAsset(
            name=facts.get("ansible_hostname", "unknown-windows"),
            hostname=facts.get("ansible_hostname", "unknown-windows"),
            ip_address=net_info.get("address", "0.0.0.0"),
            os="Windows",
            os_version=facts.get("ansible_os_version"),
            model=facts.get("ansible_product_name"),
            mac_address=net_info.get("macaddress"),
            ipv4_address=net_info.get("address"),
            ipv6_address=_get_ipv6_address(facts),
            cpu_cores=facts.get("ansible_processor_cores", 0),
            processor_type=processor_type,
            processor_count=facts.get("ansible_processor_count", 0),
            memory_mb=facts.get("ansible_memtotal_mb", 0),
            swap_total_mb=facts.get("ansible_swaptotal_mb"),
            disk_total_gb=_get_total_disk_gb(facts),
            installed_updates=facts.get("ansible_hotfixes", []),
            metadata={"source": "ansible_windows", "discovery_status": "success"}
        )
    except Exception as e:
        logger.error(f"Error parsing Windows facts: {e}")
        # Return minimal Windows asset on error
        return WindowsAsset(
            name=facts.get("ansible_hostname", "unknown_error"),
            hostname=facts.get("ansible_hostname", "unknown_error"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address", "0.0.0.0"),
            os="Windows",
            cpu_cores=0,
            memory_mb=0,
            metadata={"source": "ansible_windows", "error": str(e)}
        )


def parse_sparc_facts(facts: Dict[str, Any]) -> SparcAsset:
    """
    Parse Ansible facts into a SparcAsset.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        SparcAsset instance
    """
    try:
        processor_list = facts.get("ansible_processor", [])
        processor_type = _get_processor_type(processor_list)

        # Safely get network info
        net_info = facts.get("ansible_default_ipv4", {})
        if not isinstance(net_info, dict):
            net_info = {}

        return SparcAsset(
            name=facts.get("ansible_hostname", "unknown-sparc"),
            hostname=facts.get("ansible_hostname", "unknown-sparc"),
            ip_address=net_info.get("address", "0.0.0.0"),
            os="Solaris",
            os_version=facts.get("ansible_distribution_version"),
            model=facts.get("ansible_product_name"),
            mac_address=net_info.get("macaddress"),
            ipv4_address=net_info.get("address"),
            ipv6_address=_get_ipv6_address(facts),
            cpu_cores=facts.get("ansible_processor_cores", 0),
            processor_type=processor_type,
            processor_count=facts.get("ansible_processor_count", 0),
            memory_mb=facts.get("ansible_memtotal_mb", 0),
            swap_total_mb=facts.get("ansible_swaptotal_mb"),
            disk_total_gb=_get_total_disk_gb(facts),
            solaris_version=facts.get("ansible_distribution_version"),
            cpu_arch=facts.get("ansible_architecture"),
            metadata={"source": "ansible_sparc", "discovery_status": "success"}
        )
    except Exception as e:
        logger.error(f"Error parsing SPARC facts: {e}")
        # Return minimal SPARC asset on error
        return SparcAsset(
            name=facts.get("ansible_hostname", "unknown_error"),
            hostname=facts.get("ansible_hostname", "unknown_error"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address", "0.0.0.0"),
            os="Solaris",
            cpu_cores=0,
            memory_mb=0,
            metadata={"source": "ansible_sparc", "error": str(e)}
        )


def determine_asset_type(facts: Dict[str, Any]) -> str:
    """
    Determine the appropriate asset type based on facts.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        Asset type string ('linux', 'windows', 'sparc', 'host')
    """
    os_family = facts.get("ansible_os_family", "").lower()
    
    if os_family == "windows":
        return "windows"
    elif os_family == "solaris":
        return "sparc"
    elif os_family == "linux":
        return "linux"
    else:
        return "host"


def parse_facts_to_asset(facts: Dict[str, Any]) -> HostAsset:
    """
    Parse facts into the appropriate asset type automatically.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        Appropriate asset instance (LinuxAsset, WindowsAsset, SparcAsset, or HostAsset)
    """
    asset_type = determine_asset_type(facts)
    
    if asset_type == "linux":
        return parse_linux_facts(facts)
    elif asset_type == "windows":
        return parse_windows_facts(facts)
    elif asset_type == "sparc":
        return parse_sparc_facts(facts)
    else:
        return parse_ansible_facts(facts)
