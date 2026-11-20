#!/usr/bin/env python3
"""Tests for the local Duchamp DMA/IOMMU/firmware ownership audit."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/audit-duchamp-dma-iommu-ownership.py"
SPEC = importlib.util.spec_from_file_location("dma_ownership_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SHELL_REPORT = REPO / "research/mt6897-shell-runtime/live-20261101-v7/result.json"
RUNTIME_REPORT = REPO / "research/mt6897-live-evidence/14480520-210535/runtime-report-v7.json"
PROBE_REPORT = REPO / "research/mt6897-dma-ownership/live-probe-20261101-v1/result.json"
CLIENT_AUDIT = REPO / "research/mt6897-routing/client-audit-v1/result.json"
FIRMWARE_AUDIT = REPO / "research/mt6897-firmware-live/20261101-v1/ufs-sip-audit-v2.json"
SAVED = REPO / "research/mt6897-contract/saved-v1"
SOURCES = REPO / "research/mt6897-contract/sources"
IOMEM = REPO / "research/mt6897-shell-runtime/live-20261101-v7/root-iomem.stdout.txt"


class DmaOwnershipAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = json.loads(SHELL_REPORT.read_text(encoding="utf-8"))
        cls.runtime = json.loads(RUNTIME_REPORT.read_text(encoding="utf-8"))
        cls.probe = json.loads(PROBE_REPORT.read_text(encoding="utf-8"))
        cls.client = json.loads(CLIENT_AUDIT.read_text(encoding="utf-8"))
        cls.firmware = json.loads(FIRMWARE_AUDIT.read_text(encoding="utf-8"))
        cls.iomem = IOMEM.read_text(encoding="utf-8")
        cls.config = (SAVED / "kernel.config").read_text(encoding="utf-8")
        cls.sources = MODULE.verify_sources(REPO, SOURCES, cls.client)
        cls.dma_client = MODULE.inspect_saved_dma_client(
            SAVED / "ufs-mediatek-mod.ko"
        )

    def run_audit(self, **changes):
        values = {
            "shell": copy.deepcopy(self.shell),
            "runtime": copy.deepcopy(self.runtime),
            "probe": copy.deepcopy(self.probe),
            "client_audit": copy.deepcopy(self.client),
            "firmware": copy.deepcopy(self.firmware),
            "iomem_text": self.iomem,
            "config_text": self.config,
            "dma_client": copy.deepcopy(self.dma_client),
            "source_receipts": copy.deepcopy(self.sources),
        }
        values.update(changes)
        return MODULE.audit(**values)

    def test_runtime_probe_proves_exact_masks_and_36_bit_bus_limit(self):
        report = self.run_audit()
        self.assertTrue(report["audit_passed"])
        self.assertEqual(report["report_version"], 2)
        self.assertEqual(
            report["dma_masks"]["effective_streaming_mask"],
            "0xffffffffffffffff",
        )
        self.assertEqual(
            report["dma_masks"]["effective_streaming_mask_bits"], 64
        )
        self.assertEqual(
            report["dma_masks"]["effective_coherent_mask"],
            "0xffffffffffffffff",
        )
        self.assertEqual(report["dma_masks"]["effective_coherent_mask_bits"], 64)
        self.assertEqual(
            report["dma_masks"]["bus_dma_limit"], "0x0000000fffffffff"
        )
        self.assertEqual(report["dma_masks"]["bus_dma_limit_bits"], 36)
        self.assertTrue(report["dma_masks"]["exact_masks_proven"])

    def test_runtime_probe_selects_dma_direct_without_promoting_physical_bypass(self):
        report = self.run_audit()
        route = report["iommu_route"]
        self.assertFalse(route["dt_iommus_present"])
        self.assertFalse(route["linux_iommu_group_attached"])
        self.assertTrue(route["runtime_dma_ops_state_observed"])
        self.assertFalse(route["runtime_dma_ops_present"])
        self.assertTrue(route["runtime_iommu_fwspec_state_observed"])
        self.assertFalse(route["runtime_iommu_fwspec_present"])
        self.assertTrue(route["runtime_iommu_domain_state_observed"])
        self.assertFalse(route["runtime_iommu_domain_present"])
        self.assertTrue(route["linux_iommu_attachment_absent_at_observation"])
        self.assertTrue(route["custom_dma_ops_pointer_excluded_at_observation"])
        self.assertFalse(route["custom_platform_dma_fixup_excluded"])
        self.assertEqual(route["linux_dma_api_path"], "generic dma-direct")
        self.assertTrue(route["device_swiotlb_pool_present"])
        self.assertFalse(route["swiotlb_transfer_observed"])
        self.assertFalse(route["physical_iommu_bypass_verified"])

    def test_tampered_probe_mask_is_rejected(self):
        probe = copy.deepcopy(self.probe)
        probe["contract"]["streaming_dma_mask"] = "0x00000000ffffffff"
        with self.assertRaisesRegex(ValueError, "runtime probe contract differs"):
            self.run_audit(probe=probe)

    def test_probe_iommu_domain_appearance_is_rejected(self):
        probe = copy.deepcopy(self.probe)
        probe["contract"]["iommu_domain_present"] = True
        with self.assertRaisesRegex(ValueError, "runtime probe contract differs"):
            self.run_audit(probe=probe)

    def test_probe_cleanup_failure_is_rejected(self):
        probe = copy.deepcopy(self.probe)
        probe["execution"]["module_unloaded"] = False
        with self.assertRaisesRegex(ValueError, "runtime probe execution differs"):
            self.run_audit(probe=probe)

    def test_overlapping_power_controller_is_not_exclusive_ownership(self):
        report = self.run_audit()
        ownership = report["firmware_ownership"]
        self.assertTrue(ownership["runtime_rtff_mtcmos_cap_observed"])
        self.assertEqual(
            ownership["linux_overlapping_resource"]["start"], "0x1c001000"
        )
        self.assertFalse(ownership["exclusive_linux_ownership_proven"])
        self.assertFalse(ownership["exclusive_firmware_ownership_proven"])
        self.assertFalse(ownership["runtime_physical_effect_observed"])

    def test_missing_hccap_64as_is_rejected(self):
        shell = copy.deepcopy(self.shell)
        proc = shell["runtime_ufs_contract"]["hccap"]["proc_debug"]
        proc["effective_host_capabilities"] = "0x54c7051f"
        with self.assertRaisesRegex(ValueError, "HCCAP differs"):
            self.run_audit(shell=shell)

    def test_new_dt_iommu_attachment_requires_audit_update(self):
        runtime = copy.deepcopy(self.runtime)
        runtime["dma"]["dt_iommu_binding_declared"] = True
        with self.assertRaisesRegex(ValueError, "unexpectedly declares an IOMMU"):
            self.run_audit(runtime=runtime)

    def test_captured_runtime_mask_requires_audit_update(self):
        shell = copy.deepcopy(self.shell)
        shell["runtime_ufs_contract"]["streaming_dma_mask_bits"]["value"] = 64
        with self.assertRaisesRegex(ValueError, "unexpectedly captured"):
            self.run_audit(shell=shell)

    def test_dma_api_debug_config_change_is_rejected(self):
        config = self.config.replace(
            "# CONFIG_DMA_API_DEBUG is not set", "CONFIG_DMA_API_DEBUG=y"
        )
        with self.assertRaisesRegex(ValueError, "DMA API debug"):
            self.run_audit(config_text=config)

    def test_promoted_saved_client_flow_is_rejected(self):
        dma_client = copy.deepcopy(self.dma_client)
        dma_client["control_flow"]["coherent_setter_return_checked"] = True
        with self.assertRaisesRegex(ValueError, "client control flow differs"):
            self.run_audit(dma_client=dma_client)

    def test_nonoverlapping_iomem_is_rejected(self):
        iomem = self.iomem.replace(
            "1c001000-1c001fff : 1c001000.power-controller power-controller@1c001000",
            "1c002000-1c002fff : 1c002000.power-controller power-controller@1c002000",
        )
        with self.assertRaisesRegex(ValueError, "covering firmware MMIO"):
            self.run_audit(iomem_text=iomem)

    def test_tampered_saved_module_is_rejected(self):
        raw = bytearray((SAVED / "ufs-mediatek-mod.ko").read_bytes())
        raw[-1] ^= 1
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ufs-mediatek-mod.ko"
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                MODULE.inspect_saved_dma_client(path)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "existing"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(output),
                    "--shell-report",
                    str(SHELL_REPORT),
                    "--runtime-report",
                    str(RUNTIME_REPORT),
                    "--probe-report",
                    str(PROBE_REPORT),
                    "--client-audit",
                    str(CLIENT_AUDIT),
                    "--firmware-audit",
                    str(FIRMWARE_AUDIT),
                    "--saved-contract",
                    str(SAVED),
                    "--sources",
                    str(SOURCES),
                    "--iomem",
                    str(IOMEM),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
