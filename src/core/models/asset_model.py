from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class AssetBase(BaseModel):
    name: str
    type: str
    source: str = "ansible"
    metadata: Dict[str, str] = Field(default_factory=dict)


class HostAsset(AssetBase):
    name: str
    hostname: str
    ip_address: Optional[str]
    os: Optional[str]
    cpu_cores: Optional[int]
    memory_mb: Optional[int]
    tags: List[str] = Field(default_factory=list)


class LinuxAsset(HostAsset):
    distro: Optional[str]
    kernel_version: Optional[str]
    package_count: Optional[int]


class WindowsAsset(HostAsset):
    os_version: Optional[str]
    installed_updates: Optional[List[str]]


class SparcAsset(HostAsset):
    solaris_version: Optional[str]
    cpu_arch: Optional[str]


class ApplicationAsset(AssetBase):
    app_name: str
    version: Optional[str]
    dependencies: List[str] = Field(default_factory=list)
