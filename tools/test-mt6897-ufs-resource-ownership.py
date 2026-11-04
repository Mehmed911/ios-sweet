#!/usr/bin/env python3
"""Test the fail-closed MT6897 UFS resource-ownership candidate."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools/assess-mt6897-ufs-resource-ownership.py"
FDT = REPO.parent / "phone-fdt.bin"
RUNTIME = REPO / "research/mt6897-dma-ownership/live-20261101-v2/result.json"
FIRMWARE = REPO / "research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json"
LIVE_RUNTIME = (
    REPO
    / "research/mt6897-live-evidence/14480520-210535/runtime-report-v7.json"
)

SPEC = importlib.util.spec_from_file_location("mt6897_ufs_resource_ownership", TOOL)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load resource-ownership tool")
MODULE = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(MODULE)


class ResourceOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = MODULE.build_report(
            REPO, FDT, RUNTIME, FIRMWARE, LIVE_RUNTIME
        )

    def test_exact_mmio_manifest_is_declaration_only(self):
        mmio = self.report["declarations"]["mmio"]
        self.assertEqual(len(mmio), 18)
        observed = {entry["id"]: entry for entry in mmio}
        self.assertEqual(observed["ufs_hci"]["base"], "0x112b0000")
        self.assertEqual(observed["ufs_hci"]["bytes"], "0x3000")
        self.assertEqual(observed["ufs_phy"]["base"], "0x112a0000")
        self.assertEqual(observed["clock_hw_voter"]["base"], "0x10320000")
        self.assertEqual(observed["secure_power_controller"]["base"], "0x1c001000")
        self.assertEqual(observed["gicd"]["base"], "0xc400000")
        self.assertEqual(observed["gicr"]["base"], "0xc440000")
        for entry in mmio:
            self.assertTrue(entry["declaration_proven"])
            self.assertEqual(entry["runtime_owner"], "unproven")
            self.assertFalse(entry["xnu_physical_access_authorized"])
        unlinked = self.report["declarations"]["unlinked_ufs_named_mmio"]
        self.assertEqual(len(unlinked), 9)
        for resource_id in unlinked:
            self.assertFalse(observed[resource_id]["host_dependency_link_proven"])

    def test_exact_interrupt_clock_reset_phy_and_supply_manifest(self):
        declarations = self.report["declarations"]
        self.assertEqual(len(declarations["clocks"]), 12)
        self.assertEqual(len(declarations["resets"]), 3)
        self.assertEqual(len(declarations["interrupts"]), 9)
        self.assertEqual(
            tuple(tuple(entry["specifier"]) for entry in declarations["interrupts"]),
            MODULE.EXPECTED_INTERRUPTS,
        )
        self.assertEqual(declarations["phy"]["provider"], "/soc/ufsphy@112a0000")
        self.assertEqual(declarations["clock_hw_voter"], "/syscon@10320000")
        self.assertEqual(
            {name: value["provider"] for name, value in declarations["supplies"].items()},
            MODULE.EXPECTED_SUPPLIES,
        )
        self.assertFalse(declarations["dma_coherent"])
        self.assertFalse(declarations["iommu_binding_present"])

    def test_linux_irq_mapping_and_delivery_do_not_promote_xnu_ownership(self):
        observed = self.report["runtime_observations"]
        self.assertTrue(observed["linux_ufs_irq_mapping_proven"])
        self.assertTrue(observed["linux_ufs_irq_delivery_observed"])
        self.assertEqual(observed["linux_ufs_irq_total_delta"], 47)
        self.assertEqual(observed["linux_ufs_irq_rows_with_delivery"], 7)
        self.assertFalse(observed["xnu_ufs_irq_delivery_observed"])
        self.assertFalse(observed["xnu_ufs_irq_delegation_proven"])
        self.assertFalse(observed["ufs_interrupt_ownership_proven"])
        self.assertFalse(self.report["runtime_proofs"]["ufs_interrupt_ownership"])

    def test_static_firmware_path_never_becomes_runtime_ownership(self):
        firmware = self.report["firmware_contract"]
        self.assertTrue(firmware["captured_bl31_artifact_pinned"])
        self.assertTrue(firmware["static_service_dispatch_proven"])
        self.assertEqual(firmware["service_id"], "0xc2000276")
        self.assertEqual(firmware["selectors"], MODULE.UFS_SELECTORS)
        self.assertFalse(firmware["installed_firmware_identity_proven"])
        self.assertFalse(firmware["runtime_effect_contract_proven"])
        self.assertFalse(firmware["exclusive_owner_proven"])
        self.assertFalse(firmware["direct_xnu_secure_power_mmio_authorized"])

    def test_current_evidence_denies_every_physical_callback(self):
        receipt = self.report["ownership_receipt"]
        self.assertEqual(receipt["status"], "denied")
        self.assertFalse(receipt["receipt_issuable"])
        self.assertIsNone(receipt["payload"])
        self.assertEqual(tuple(receipt["blockers"]), MODULE.RUNTIME_PROOFS)
        self.assertEqual(
            self.report["authorization"],
            {
                "physical_backend_enabled": False,
                "mmio_callbacks": 0,
                "smc_callbacks": 0,
                "dma_callbacks": 0,
                "ufs_commands": 0,
                "interrupt_reconfiguration_callbacks": 0,
            },
        )

    def test_receipt_model_is_fail_closed_for_each_missing_proof(self):
        all_true = {name: True for name in MODULE.RUNTIME_PROOFS}
        complete = MODULE.evaluate_receipt(all_true)
        self.assertTrue(complete["receipt_issuable"])
        for missing in MODULE.RUNTIME_PROOFS:
            proofs = copy.deepcopy(all_true)
            proofs[missing] = False
            receipt = MODULE.evaluate_receipt(proofs)
            self.assertFalse(receipt["receipt_issuable"], missing)
            self.assertIsNone(receipt["payload"], missing)
            self.assertEqual(receipt["blockers"], [missing])

    def test_cli_pins_inputs_preserves_output_and_stays_offline(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            command = [
                sys.executable, str(TOOL), str(output),
                "--fdt", str(FDT),
                "--runtime-evidence", str(RUNTIME),
                "--firmware-evidence", str(FIRMWARE),
                "--live-runtime-evidence", str(LIVE_RUNTIME),
            ]
            result = subprocess.run(
                command, cwd=REPO, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertFalse(report["ownership_receipt"]["receipt_issuable"])
            self.assertFalse(report["safety"]["phone_access"])
            self.assertFalse(report["safety"]["mmio_access"])
            self.assertFalse(report["safety"]["smc_execution"])
            self.assertFalse(report["safety"]["physical_backend_enabled"])
            second = subprocess.run(
                command, cwd=REPO, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("preserve existing output", second.stdout)

            changed = Path(temporary) / "runtime-changed.json"
            changed.write_bytes(RUNTIME.read_bytes() + b"\n")
            rejected = subprocess.run(
                [
                    sys.executable, str(TOOL), str(Path(temporary) / "changed.json"),
                    "--fdt", str(FDT),
                    "--runtime-evidence", str(changed),
                    "--firmware-evidence", str(FIRMWARE),
                    "--live-runtime-evidence", str(LIVE_RUNTIME),
                ],
                cwd=REPO, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("runtime evidence hash differs", rejected.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
