from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def parse_ansible_facts(facts: Dict[str, Any]) -> HostAsset:
    """
    Parse Ansible facts into a generic HostAsset.
    
    Args:
        facts: Dictionary of Ansible facts
        
    Returns:
        HostAsset instance
    """
    try:
        # Extract IP address safely
        ip_address = None
        if "ansible_default_ipv4" in facts and isinstance(facts["ansible_default_ipv4"], dict):
            ip_address = facts["ansible_default_ipv4"].get("address")
        elif "ansible_ip_addresses" in facts and isinstance(facts["ansible_ip_addresses"], list):
            ip_address = facts["ansible_ip_addresses"][0] if facts["ansible_ip_addresses"] else None
        
        return HostAsset(
            name=facts.get("ansible_hostname", "unknown"),
            type="host",
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=ip_address,
            os=facts.get("ansible_distribution", facts.get("ansible_os_family", "Unknown")),
            cpu_cores=facts.get("ansible_processor_vcpus", 1),
            memory_mb=facts.get("ansible_memtotal_mb", 1024),
            metadata={"source": "ansible_facts", "discovery_status": facts.get("discovery_status", "success")}
        )
    except Exception as e:
        logger.error(f"Error parsing Ansible facts: {e}")
        # Return minimal asset on error
        return HostAsset(
            name=facts.get("ansible_hostname", "unknown"),
            type="host",
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address") if isinstance(facts.get("ansible_default_ipv4"), dict) else None,
            os="Unknown",
            cpu_cores=1,
            memory_mb=1024,
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
        # Extract IP address safely
        ip_address = None
        if "ansible_default_ipv4" in facts and isinstance(facts["ansible_default_ipv4"], dict):
            ip_address = facts["ansible_default_ipv4"].get("address")
        elif "ansible_ip_addresses" in facts and isinstance(facts["ansible_ip_addresses"], list):
            ip_address = facts["ansible_ip_addresses"][0] if facts["ansible_ip_addresses"] else None
        
        # Extract package count safely
        package_count = None
        if "ansible_facts" in facts and isinstance(facts["ansible_facts"], dict):
            packages = facts["ansible_facts"].get("packages", [])
            if isinstance(packages, list):
                package_count = len(packages)
        
        return LinuxAsset(
            type="linux",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=ip_address,
            os=facts.get("ansible_distribution", "Linux"),
            cpu_cores=facts.get("ansible_processor_vcpus", 1),
            memory_mb=facts.get("ansible_memtotal_mb", 1024),
            distro=facts.get("ansible_distribution", "Unknown"),
            kernel_version=facts.get("ansible_kernel", "Unknown"),
            package_count=package_count,
            metadata={"source": "ansible_linux", "discovery_status": facts.get("discovery_status", "success")}
        )
    except Exception as e:
        logger.error(f"Error parsing Linux facts: {e}")
        # Return minimal Linux asset on error
        return LinuxAsset(
            type="linux",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address") if isinstance(facts.get("ansible_default_ipv4"), dict) else None,
            os="Linux",
            cpu_cores=1,
            memory_mb=1024,
            distro="Unknown",
            kernel_version="Unknown",
            package_count=None,
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
        # Extract IP address safely
        ip_address = None
        if "ansible_ip_addresses" in facts and isinstance(facts["ansible_ip_addresses"], list):
            ip_address = facts["ansible_ip_addresses"][0] if facts["ansible_ip_addresses"] else None
        elif "ansible_default_ipv4" in facts and isinstance(facts["ansible_default_ipv4"], dict):
            ip_address = facts["ansible_default_ipv4"].get("address")
        
        # Extract installed updates safely
        installed_updates = []
        if "ansible_hotfixes" in facts and isinstance(facts["ansible_hotfixes"], list):
            installed_updates = facts["ansible_hotfixes"]
        
        return WindowsAsset(
            type="windows",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=ip_address,
            os="Windows",
            cpu_cores=facts.get("ansible_processor_vcpus", 1),
            memory_mb=facts.get("ansible_memtotal_mb", 1024),
            os_version=facts.get("ansible_os_name", "Unknown"),
            installed_updates=installed_updates,
            metadata={"source": "ansible_windows", "discovery_status": facts.get("discovery_status", "success")}
        )
    except Exception as e:
        logger.error(f"Error parsing Windows facts: {e}")
        # Return minimal Windows asset on error
        return WindowsAsset(
            type="windows",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=facts.get("ansible_ip_addresses", [None])[0] if isinstance(facts.get("ansible_ip_addresses"), list) else None,
            os="Windows",
            cpu_cores=1,
            memory_mb=1024,
            os_version="Unknown",
            installed_updates=[],
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
        # Extract IP address safely
        ip_address = None
        if "ansible_default_ipv4" in facts and isinstance(facts["ansible_default_ipv4"], dict):
            ip_address = facts["ansible_default_ipv4"].get("address")
        elif "ansible_ip_addresses" in facts and isinstance(facts["ansible_ip_addresses"], list):
            ip_address = facts["ansible_ip_addresses"][0] if facts["ansible_ip_addresses"] else None
        
        return SparcAsset(
            type="sparc",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=ip_address,
            os="Solaris",
            cpu_cores=facts.get("ansible_processor_vcpus", 1),
            memory_mb=facts.get("ansible_memtotal_mb", 1024),
            solaris_version=facts.get("ansible_distribution_version", "Unknown"),
            cpu_arch=facts.get("ansible_architecture", "Unknown"),
            metadata={"source": "ansible_sparc", "discovery_status": facts.get("discovery_status", "success")}
        )
    except Exception as e:
        logger.error(f"Error parsing SPARC facts: {e}")
        # Return minimal SPARC asset on error
        return SparcAsset(
            type="sparc",
            name=facts.get("ansible_hostname", "unknown"),
            hostname=facts.get("ansible_hostname", "unknown"),
            ip_address=facts.get("ansible_default_ipv4", {}).get("address") if isinstance(facts.get("ansible_default_ipv4"), dict) else None,
            os="Solaris",
            cpu_cores=1,
            memory_mb=1024,
            solaris_version="Unknown",
            cpu_arch="Unknown",
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
    distribution = facts.get("ansible_distribution", "").lower()
    
    if os_family == "windows" or distribution == "windows":
        return "windows"
    elif os_family == "solaris" or distribution in ["solaris", "sunos"]:
        return "sparc"
    elif os_family == "linux" or distribution in ["linux", "ubuntu", "centos", "rhel", "debian", "fedora"]:
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
