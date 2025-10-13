from src.core.models.fact_parser import parse_linux_facts, parse_windows_facts, parse_sparc_facts
from src.core.models.jira_model import map_linux_to_jira, map_windows_to_jira, map_sparc_to_jira
from src.core.models.asset_model import LinuxAsset, WindowsAsset, SparcAsset

ASSET_REGISTRY = {
    "linux": {
        "parser": parse_linux_facts,
        "mapper": map_linux_to_jira,
        "model": LinuxAsset
    },
    "windows": {
        "parser": parse_windows_facts,
        "mapper": map_windows_to_jira,
        "model": WindowsAsset
    },
    "solaris": {
        "parser": parse_sparc_facts,
        "mapper": map_sparc_to_jira,
        "model": SparcAsset
    }
}


def get_parser(os_family: str):
    return ASSET_REGISTRY.get(os_family, {}).get("parser")


def get_mapper(os_family: str):
    return ASSET_REGISTRY.get(os_family, {}).get("mapper")
