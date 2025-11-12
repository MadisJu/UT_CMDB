from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class AssetBase(BaseModel):
    hostname: str
    type: str
    source: str = "ansible"
    metadata: Dict[str, str] = Field(default_factory=dict)


class HostAsset(AssetBase):
    hostname: str
    ip_address: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    model: Optional[str] = None
    mac_address: Optional[str] = None
    ipv4_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    cpu_cores: Optional[int] = None
    processor_type: Optional[str] = None
    processor_count: Optional[int] = None
    memory_mb: Optional[int] = None
    swap_total_mb: Optional[int] = None
    disk_total_gb: Optional[float] = None
    tags: List[str] = Field(default_factory=list)


class LinuxAsset(HostAsset):
    distro: Optional[str] = None
    kernel_version: Optional[str] = None
    package_count: Optional[int] = None


class WindowsAsset(HostAsset):
    os_version: Optional[str]
    installed_updates: Optional[List[str]]


class SparcAsset(HostAsset):
    solaris_version: Optional[str] = None
    cpu_arch: Optional[str] = None


class ApplicationAsset(AssetBase):
    app_name: str
    version: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
