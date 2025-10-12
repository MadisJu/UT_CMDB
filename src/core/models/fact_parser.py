from src.core.models.asset_model import HostAsset, LinuxAsset, WindowsAsset, SparcAsset


def parse_ansible_facts(facts: dict) -> HostAsset:
    return HostAsset(
        name=facts.get("ansible_hostname"),
        type="host",
        hostname=facts.get("ansible_hostname"),
        ip_address=facts.get("ansible_default_ipv4", {}).get("address"),
        os=facts.get("ansible_distribution"),
        cpu_cores=facts.get("ansible_processor_vcpus"),
        memory_mb=facts.get("ansible_memtotal_mb"),
        metadata={"source": "ansible_facts"}
    )


def parse_linux_facts(facts: dict) -> LinuxAsset:
    return LinuxAsset(
        name=facts.get("ansible_hostname"),
        hostname=facts.get("ansible_hostname"),
        ip_address=facts.get("ansible_default_ipv4", {}).get("address"),
        os_family="linux",
        distro=facts.get("ansible_distribution"),
        kernel_version=facts.get("ansible_kernel"),
        package_count=len(facts.get("ansible_facts", {}).get("packages", [])) if facts.get("ansible_facts") else None,
        metadata={"source": "ansible_linux"}
    )


def parse_windows_facts(facts: dict) -> WindowsAsset:
    return WindowsAsset(
        name=facts.get("ansible_hostname"),
        hostname=facts.get("ansible_hostname"),
        ip_address=facts.get("ansible_ip_addresses", [None])[0],
        os_family="windows",
        os_version=facts.get("ansible_os_name"),
        installed_updates=facts.get("ansible_hotfixes", []),
        metadata={"source": "ansible_windows"}
    )


def parse_sparc_facts(facts: dict) -> SparcAsset:
    return SparcAsset(
        name=facts.get("ansible_hostname"),
        hostname=facts.get("ansible_hostname"),
        ip_address=facts.get("ansible_default_ipv4", {}).get("address"),
        os_family="solaris",
        solaris_version=facts.get("ansible_distribution_version"),
        cpu_arch=facts.get("ansible_architecture"),
        metadata={"source": "ansible_sparc"}
    )
