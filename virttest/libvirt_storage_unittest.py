#!/usr/bin/python
import unittest

try:
    import autotest.common as common
except ImportError:
    import common

from autotest.client.utils import CmdResult
from virttest import libvirt_storage, virsh

VIRSH_EXEC = virsh.VIRSH_EXEC

# Ensure the following tests ONLY run if a valid virsh command exists #####


class ModuleLoadCheckVirsh(unittest.TestCase):
    import virsh

    def run(self, *args, **dargs):
        test_virsh = self.virsh.Virsh()
        if test_virsh['virsh_exec'] == '/bin/true':
            return  # Don't run any tests, no virsh executable was found
        else:
            super(ModuleLoadCheckVirsh, self).run(*args, **dargs)

# The output of virsh.pool_list with only default pool
_DEFAULT_POOL = ("Name                 State      Autostart\n"
                 "-----------------------------------------\n"
                 "default              active      yes    \n")

# Set output of virsh.pool_list
global _pools_output
_pools_output = _DEFAULT_POOL


class PoolTestBase(ModuleLoadCheckVirsh):

    @staticmethod
    def _pool_list(option="--all", **dargs):
        # Bogus output of virsh commands
        cmd = "virsh pool-list --all"
        output = _pools_output
        return CmdResult(cmd, output)

    @staticmethod
    def _pool_info(name="default", **dargs):
        cmd = "virsh pool-info %s" % name
        default_output = (
            "Name:           default\n"
            "UUID:           bfe5d630-ec5d-86c2-ecca-8a5210493db7\n"
            "State:          running\n"
            "Persistent:     yes\n"
            "Autostart:      yes\n"
            "Capacity:       47.93 GiB\n"
            "Allocation:     36.74 GiB\n"
            "Available:      11.20 GiB\n")
        if name == "default":
            return CmdResult(cmd, default_output)
        else:
            return CmdResult(cmd)

    @staticmethod
    def _pool_define_as(name="unittest", pool_type="dir",
                        target="/var/tmp", **dargs):
        unittest_pool = "unittest             inactive    no\n"
        global _pools_output
        _pools_output = _DEFAULT_POOL + unittest_pool
        return True

    @staticmethod
    def _pool_build(name="unittest", **dargs):
        return True

    @staticmethod
    def _pool_start(name="unittest", **dargs):
        unittest_pool = "unittest             active     no\n"
        global _pools_output
        _pools_output = _DEFAULT_POOL + unittest_pool
        return True

    @staticmethod
    def _pool_autostart(name="unittest", **dargs):
        unittest_pool = "unittest             active     yes\n"
        global _pools_output
        _pools_output = _DEFAULT_POOL + unittest_pool
        return True

    @staticmethod
    def _pool_destroy(name="unittest", **dargs):
        unittest_pool = "unittest             inactive    yes\n"
        global _pools_output
        _pools_output = _DEFAULT_POOL + unittest_pool
        return True

    @staticmethod
    def _pool_undefine(name="unittest", **dargs):
        global _pools_output
        _pools_output = _DEFAULT_POOL
        return True

    def setUp(self):
        # To avoid not installed libvirt packages
        self.bogus_virsh = virsh.Virsh(virsh_exec=virsh.VIRSH_EXEC,
                                       uri='qemu:///system', debug=True,
                                       ignore_status=True)

        # Use defined virsh methods above
        self.bogus_virsh.super_set('pool_list', self._pool_list)
        self.bogus_virsh.super_set('pool_info', self._pool_info)
        self.bogus_virsh.super_set('pool_define_as', self._pool_define_as)
        self.bogus_virsh.super_set('pool_build', self._pool_build)
        self.bogus_virsh.super_set('pool_start', self._pool_start)
        self.bogus_virsh.super_set('pool_destroy', self._pool_destroy)
        self.bogus_virsh.super_set('pool_undefine', self._pool_undefine)
        self.bogus_virsh.super_set('pool_autostart', self._pool_autostart)
        self.sp = libvirt_storage.StoragePool(virsh_instance=self.bogus_virsh)


class ExistPoolTest(PoolTestBase):

    def test_exist_pool(self):
        pools = self.sp.list_pools()
        self.assertIsInstance(pools, dict)
        # Test pool_state
        self.assertIn(self.sp.pool_state("default"), ['active', 'inactive'])
        # Test pool_info
        self.assertNotEqual(self.sp.pool_info("default"), {})


class NewPoolTest(PoolTestBase):

    def test_dir_pool(self):
        # Used for auto cleanup
        self.pool_name = "unittest"
        global _pools_output
        self.assertTrue(self.sp.define_dir_pool(self.pool_name, "/var/tmp"))
        self.assertTrue(self.sp.build_pool(self.pool_name))
        self.assertTrue(self.sp.start_pool(self.pool_name))
        self.assertTrue(self.sp.set_pool_autostart(self.pool_name))
        self.assertTrue(self.sp.delete_pool(self.pool_name))

    def tearDown(self):
        # Confirm created pool has been cleaned up
        self.sp.delete_pool(self.pool_name)


class NotExpectedPoolTest(PoolTestBase):

    def test_not_exist_pool(self):
        self.assertFalse(self.sp.pool_exists("NOTEXISTPOOL"))
        self.assertIsNone(self.sp.pool_state("NOTEXISTPOOL"))
        self.assertEqual(self.sp.pool_info("NOTEXISTPOOL"), {})


if __name__ == "__main__":
    unittest.main()