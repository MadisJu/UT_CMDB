import unittest
from src.core.services.machine_inventory import MachineInventory

class TestMachineInventory(unittest.TestCase):
    """
    Unit tests for the MachineInventory service.
    Tests the parsing and querying of the Ansible inventory structure.
    """

    def setUp(self):
        """Set up a mock inventory structure for testing."""
        self.mock_inventory = {
            "all": {
                "hosts": {"host1": {}, "host2": {}}
            },
            "webservers": {
                "hosts": {"host1": {}}
            },
            "dbservers": {
                "hosts": {"host2": {}}
            },
            "group_with_vars": {
                "hosts": {
                    "host3": {"ansible_host": "1.2.3.4", "ansible_user": "admin"}
                }
            }
        }
        self.inventory = MachineInventory(parsed_inventory=self.mock_inventory)

    def test_get_all_machines(self):
        """Test retrieval of all unique hostnames from the 'all' group."""
        machines = self.inventory.get_all_machines()
        self.assertEqual(set(machines), {"host1", "host2"})

    def test_get_machines_by_group(self):
        """Test retrieval of hostnames belonging to specific groups."""
        webservers = self.inventory.get_machines_by_group("webservers")
        self.assertEqual(webservers, ["host1"])
        
        dbservers = self.inventory.get_machines_by_group("dbservers")
        self.assertEqual(dbservers, ["host2"])
        
        unknown = self.inventory.get_machines_by_group("unknown")
        self.assertEqual(unknown, [])

    def test_get_host_vars(self):
        """Test retrieval of host-specific variables (e.g., ansible_host)."""
        vars = self.inventory.get_host_vars("host3")
        self.assertEqual(vars, {"ansible_host": "1.2.3.4", "ansible_user": "admin"})
        
        vars_unknown = self.inventory.get_host_vars("unknown_host")
        self.assertEqual(vars_unknown, {})

    def test_get_target_hosts_with_users(self):
        """Test retrieval of (host, user) tuples for Ansible execution."""
        targets = self.inventory.get_target_hosts_with_users(group="group_with_vars")
        self.assertEqual(targets, [("host3", "admin")])
        
        targets_default = self.inventory.get_target_hosts_with_users(group="webservers", default_user="ubuntu")
        self.assertEqual(targets_default, [("host1", "ubuntu")])

    def test_get_inventory_summary(self):
        """Test generation of inventory statistics (counts per group)."""
        summary = self.inventory.get_inventory_summary()
        self.assertEqual(summary["total_hosts"], 2) # host1, host2 (host3 is not in 'all' in my mock, wait)
        # get_all_machines returns hosts from 'all' group.
        # In my mock, 'all' has host1, host2. host3 is only in group_with_vars.
        # So total_hosts is 2.
        
        self.assertIn("webservers", summary["group_counts"])
        self.assertEqual(summary["group_counts"]["webservers"], 1)


if __name__ == '__main__':
    unittest.main()
