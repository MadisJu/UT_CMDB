import unittest
from src.core.models.fact_parser import (
    _get_total_disk_gb,
    _get_ipv6_address,
    _get_processor_type,
    determine_asset_type,
    parse_facts_to_asset,
    parse_linux_facts,
    parse_windows_facts
)
from src.core.models.asset_model import LinuxAsset, WindowsAsset, HostAsset

class TestFactParser(unittest.TestCase):
    """
    Unit tests for the fact parser module.
    Tests the extraction and normalization of Ansible facts into internal Asset models.
    """

    def test_get_total_disk_gb_ansible_devices(self):
        """Test calculation of total disk space from ansible_devices."""
        facts = {
            "ansible_devices": {
                "sda": {"size_bytes": "10737418240"},  # 10 GB
                "sdb": {"size_bytes": "21474836480"},  # 20 GB
                "loop0": {"size_bytes": "1000"} # Should be ignored
            }
        }
        # Total 30 GB
        self.assertEqual(_get_total_disk_gb(facts), 30.0)

    def test_get_total_disk_gb_ansible_mounts(self):
        """Test calculation of total disk space from ansible_mounts (fallback)."""
        facts = {
            "ansible_mounts": [
                {"device": "/dev/sda1", "size_total": 10737418240}, # 10 GB
                {"device": "/dev/sdb1", "size_total": 21474836480}, # 20 GB
                {"device": "tmpfs", "size_total": 1000} # Should be ignored
            ]
        }
        self.assertEqual(_get_total_disk_gb(facts), 30.0)

    def test_get_total_disk_gb_ansible_disks(self):
        """Test calculation of total disk space from ansible_disks (Windows)."""
        facts = {
            "ansible_disks": [
                {"size": 10737418240}, # 10 GB
                {"size": 21474836480}  # 20 GB
            ]
        }
        self.assertEqual(_get_total_disk_gb(facts), 30.0)

    def test_get_total_disk_gb_empty(self):
        """Test disk calculation with empty facts returns 0."""
        self.assertEqual(_get_total_disk_gb({}), 0)

    def test_get_ipv6_address(self):
        """Test extraction of the first global IPv6 address."""
        facts = {
            "ansible_all_ipv6_addresses": [
                {"address": "fe80::1", "scope": "link"},
                {"address": "2001:db8::1", "scope": "global"}
            ]
        }
        self.assertEqual(_get_ipv6_address(facts), "2001:db8::1")

    def test_get_ipv6_address_none(self):
        """Test IPv6 extraction returns None when no addresses exist."""
        facts = {"ansible_all_ipv6_addresses": []}
        self.assertIsNone(_get_ipv6_address(facts))

    def test_get_processor_type(self):
        """Test normalization of processor type strings."""
        self.assertEqual(_get_processor_type(["Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz"]), "Intel(R) Core(TM) i7-8550U CPU @ 1.80GHz")
        self.assertEqual(_get_processor_type(["AMD Ryzen 5 3600 6-Core Processor"]), "AMD Ryzen 5 3600 6-Core Processor")
        self.assertEqual(_get_processor_type([]), "N/A")

    def test_determine_asset_type(self):
        """Test logic for determining asset type based on OS family."""
        self.assertEqual(determine_asset_type({"ansible_os_family": "RedHat"}), "linux")
        self.assertEqual(determine_asset_type({"ansible_os_family": "Windows"}), "windows")
        self.assertEqual(determine_asset_type({"ansible_os_family": "Solaris"}), "sparc")
        self.assertEqual(determine_asset_type({"ansible_os_family": "Unknown"}), "host")

    def test_parse_linux_facts(self):
        """Test parsing of Linux-specific facts into LinuxAsset model."""
        facts = {
            "ansible_hostname": "test-linux",
            "ansible_default_ipv4": {"address": "192.168.1.10", "macaddress": "00:11:22:33:44:55"},
            "ansible_distribution": "Ubuntu",
            "ansible_distribution_version": "20.04",
            "ansible_processor_cores": 4,
            "ansible_memtotal_mb": 8192,
            "ansible_os_family": "Debian"
        }
        asset = parse_facts_to_asset(facts)
        self.assertIsInstance(asset, LinuxAsset)
        self.assertEqual(asset.hostname, "test-linux")
        self.assertEqual(asset.ipv4_address, "192.168.1.10")
        self.assertEqual(asset.os, "Ubuntu")

    def test_parse_windows_facts(self):
        """Test parsing of Windows-specific facts into WindowsAsset model."""
        facts = {
            "ansible_hostname": "test-windows",
            "ansible_default_ipv4": {"address": "192.168.1.20"},
            "ansible_os_family": "Windows",
            "ansible_os_version": "10.0.19041",
            "ansible_processor_cores": 2,
            "ansible_memtotal_mb": 4096
        }
        asset = parse_facts_to_asset(facts)
        self.assertIsInstance(asset, WindowsAsset)
        self.assertEqual(asset.hostname, "test-windows")
        self.assertEqual(asset.os, "Windows")

    def test_parse_generic_facts(self):
        """Test parsing of generic/unknown facts into HostAsset model."""
        facts = {
            "ansible_hostname": "test-generic",
            "ansible_os_family": "Unknown"
        }
        asset = parse_facts_to_asset(facts)
        self.assertIsInstance(asset, HostAsset)
        self.assertEqual(asset.hostname, "test-generic")

if __name__ == '__main__':
    unittest.main()
