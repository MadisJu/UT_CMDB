from src.core.models.asset_model import HostAsset


def map_host_to_jira(asset: HostAsset) -> dict:
    return {
        "objectTypeId": "10004",  # This is for non specific hosts
        "attributes": [
            {"name": "Hostname", "value": asset.hostname},
            {"name": "IP Address", "value": asset.ip_address},
            {"name": "Operating System", "value": asset.os},
            {"name": "CPU Cores", "value": asset.cpu_cores},
            {"name": "Memory (MB)", "value": asset.memory_mb},
        ]
    }


def map_linux_to_jira(asset):
    return {
        "objectTypeId": "10001",
        "attributes": [
            {"name": "Hostname", "value": asset.hostname},
            {"name": "IP", "value": asset.ip_address},
            {"name": "Distribution", "value": asset.distro},
            {"name": "Kernel Version", "value": asset.kernel_version},
        ]
    }


def map_windows_to_jira(asset):
    return {
        "objectTypeId": "10002",
        "attributes": [
            {"name": "Hostname", "value": asset.hostname},
            {"name": "IP", "value": asset.ip_address},
            {"name": "OS Version", "value": asset.os_version},
        ]
    }


def map_sparc_to_jira(asset):
    return {
        "objectTypeId": "10003",
        "attributes": [
            {"name": "Hostname", "value": asset.hostname},
            {"name": "Solaris Version", "value": asset.solaris_version},
            {"name": "Architecture", "value": asset.cpu_arch},
        ]
    }
