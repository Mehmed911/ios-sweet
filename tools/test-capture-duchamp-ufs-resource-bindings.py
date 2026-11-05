#!/usr/bin/env python3
import copy
import importlib.util
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/capture-duchamp-ufs-resource-bindings.py"
SPEC = importlib.util.spec_from_file_location("resource_bindings", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(MODULE)


def fixture():
    bindings = {
        key: {
            "path": value["path"],
            "driver": value["driver"],
            "runtime_status": value["runtime_status"],
        }
        for key, value in MODULE.EXPECTED_BINDINGS.items()
    }
    modules = []
    for names in MODULE.REQUIRED_MODULES.values():
        for name in names:
            modules.append(f"{name} 4096 0 - Live 0x0 (OE)")
    suppliers = [
        MODULE.UFS_DEVICE + "/supplier:phy:phy-112a0000.ufsphy.3",
        MODULE.UFS_DEVICE + "/supplier:platform:10000000.syscon",
        MODULE.UFS_DEVICE + "/supplier:platform:112a0000.ufsphy",
        MODULE.UFS_DEVICE + "/supplier:platform:112b8000.syscon",
        MODULE.UFS_DEVICE + "/supplier:platform:112b8000.syscon:reset-controller",
        MODULE.UFS_DEVICE + "/supplier:platform:112bb000.syscon",
        MODULE.UFS_DEVICE + "/supplier:platform:112bb000.syscon:reset-controller",
        MODULE.UFS_DEVICE + "/supplier:platform:1c00f000.dvfsrc",
        MODULE.UFS_DEVICE + "/supplier:platform:1cc04000.spmi",
        MODULE.UFS_DEVICE + "/supplier:platform:1cc04000.spmi:mt6319@8:mt6319-8-regulator",
        MODULE.UFS_DEVICE + "/supplier:regulator:regulator.9",
        MODULE.UFS_DEVICE + "/supplier:regulator:regulator.31",
        MODULE.UFS_DEVICE + "/supplier:regulator:regulator.74",
    ]
    irq_rows = []
    for irq, hwirq in zip(range(500, 509),
                          (200, 209, 210, 211, 212, 213, 214, 215, 216)):
        irq_rows.append(
            f"{irq}: 0 0 0 0 0 0 0 0 GICv3 {hwirq} Level ufshcd"
        )
    return {
        "captured_at_utc": "2026-11-05T00:00:00+00:00",
        "serial": "TEST",
        "device": "duchamp",
        "hardware": "mt6897",
        "slot_suffix": "_a",
        "root_id": "uid=0(root) gid=0(root)",
        "bindings": bindings,
        "hw_voter": {
            "path": MODULE.HW_VOTER_PATH,
            "compatibles": list(MODULE.HW_VOTER_COMPATIBLES),
            "driver": None,
        },
        "regulators": {
            "mt6363_vemc": {
                "sysfs_id": 31, "state": "enabled", "microvolts": 2500000,
                "device": "/sys/devices/platform/soc/1cc04000.spmi/spmi-0/0-04",
            },
            "dvfsrc-vcore": {
                "sysfs_id": 74, "state": None, "microvolts": 800000,
                "device": "/sys/devices/platform/soc/1c00f000.dvfsrc",
            },
            "8_vbuck3": {
                "sysfs_id": 9, "state": "enabled", "microvolts": 1193750,
                "device": "/sys/devices/platform/soc/1cc04000.spmi/spmi-0/0-08",
            },
        },
        "supplier_links": suppliers,
        "proc_modules": "\n".join(modules),
        "proc_interrupts": "\n".join(irq_rows),
    }


class ResourceBindingCaptureTests(unittest.TestCase):
    def test_linux_bindings_do_not_promote_xnu_authorization(self):
        report = MODULE.analyze_snapshot(fixture())
        self.assertTrue(report["passed"])
        boundary = report["proof_boundary"]
        self.assertTrue(boundary["linux_current_provider_bindings_proven"])
        self.assertTrue(boundary["linux_ufs_regulator_state_observed"])
        self.assertTrue(boundary["slb_and_scmi_coordination_modules_loaded"])
        self.assertTrue(boundary["firewall_and_protection_modules_loaded"])
        self.assertFalse(boundary["system_cache_exclusive_owner_proven"])
        self.assertFalse(boundary["ufs_cache_maintenance_reachability_proven"])
        self.assertFalse(boundary["runtime_smc_effect_proven"])
        self.assertFalse(boundary["firewall_state_or_ufs_grant_proven"])
        self.assertFalse(boundary[
            "xnu_mmio_clock_reset_phy_regulator_irq_delegation_proven"
        ])
        self.assertEqual(report["authorization"]["mmio_callbacks"], 0)
        self.assertFalse(report["authorization"]["physical_backend_enabled"])

    def test_missing_driver_binding_is_rejected(self):
        snapshot = fixture()
        snapshot["bindings"]["ufs_phy"]["driver"] = None
        with self.assertRaisesRegex(ValueError, "ufs_phy driver differs"):
            MODULE.analyze_snapshot(snapshot)

    def test_system_cache_supplier_promotion_is_rejected(self):
        snapshot = fixture()
        snapshot["supplier_links"][0] = (
            MODULE.UFS_DEVICE + "/supplier:platform:10342000.system-cache"
        )
        with self.assertRaisesRegex(ValueError, "SLB/system-cache"):
            MODULE.analyze_snapshot(snapshot)

    def test_missing_firewall_module_is_rejected(self):
        snapshot = fixture()
        snapshot["proc_modules"] = snapshot["proc_modules"].replace(
            "device_apc_mt6897 4096 0 - Live 0x0 (OE)\n", ""
        )
        with self.assertRaisesRegex(ValueError, "firewall_and_protection"):
            MODULE.analyze_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
