#!/usr/bin/env python3
"""Tests for the fail-closed Duchamp phone-readiness assessment."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/assess-duchamp-mt6897-phone-readiness.py"
SPEC = importlib.util.spec_from_file_location("duchamp_phone_readiness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixtures():
    live = {
        "report_version": 1,
        "result": {"passed": True},
        "fdt": {
            "reference_sha256": MODULE.FDT_SHA256,
            "critical_topology_matches_reference": True,
            "added_nodes": [],
            "removed_nodes": [],
        },
        "runtime": {
            "timer": {
                "android_runtime_delivery_observed": True,
                "xnu_phone_delivery_observed": False,
                "clocksource": "arch_sys_counter",
                "clockevent": "arch_sys_timer",
                "gic_hwirq": 27,
                "total_delta": 1,
            },
            "ufs": {
                "android_runtime_delivery_observed": True,
                "xnu_phone_delivery_observed": False,
                "driver": "/sys/bus/platform/drivers/ufshcd-mtk",
                "expected_gic_hwirqs": MODULE.UFS_HWIRQS,
                "total_delta": 1,
                "installed_module": {
                    "name": "ufs_mediatek_mod",
                    "state": "Live",
                    "gnu_build_id": MODULE.UFS_MODULE_BUILD_ID,
                    "local_source_commit_match_verified": False,
                    "saved_vendor_module": {
                        "sha256": MODULE.UFS_MODULE_SHA256,
                        "gnu_build_id": MODULE.UFS_MODULE_BUILD_ID,
                        "build_id_match_verified": True,
                        "source_commit_match_verified": False,
                    },
                },
            },
        },
        "firmware": {
            "installed_scmi_identity_observed": True,
            "installed_ufs_client_binary_identity_verified": True,
            "installed_ufs_sip_abi_verified": False,
            "installed_ufs_sip_effect_contract_verified": False,
            "xnu_firmware_abi_verified": False,
            "physical_resource_ownership_verified": False,
        },
        "dma": {
            "dt_direct_dma_windows": [{
                "path": "/soc",
                "child_bus_start": "0x0",
                "parent_bus_start": "0x0",
                "bytes": "0x1000000000",
                "identity": True,
            }],
            "dt_iommu_binding_declared": False,
            "linux_sysfs_iommu_group_attached": False,
            "linux_iommu_supplier_links": [],
            "physical_dma_bypass_verified": False,
            "coherency_verified": False,
            "xnu_dma_ready": False,
        },
        "safety": {
            "offline_analysis_only": True,
            "read_only_inputs": True,
            "adb_access_by_this_tool": False,
            "mmio_access": False,
            "phone_write": False,
            "partition_access": False,
        },
    }
    offline = {
        "passed": True,
        "inputs_unchanged": True,
        "input_sha256": {"fdt": MODULE.FDT_SHA256},
        "safety": {
            "physical_device_access": False,
            "mmio_access": False,
            "flash_or_partition_write": False,
            "phone_execution_authorized": False,
        },
        "remaining_physical_blockers": {
            "installed_firmware_contract": "unverified",
            "physical_ufs_backend": "disabled",
            "ufs_topckgen_physical_backend": "disabled",
        },
    }
    saved = {
        "audit_complete": True,
        "input_sha256": {"fdt": MODULE.FDT_SHA256},
        "modules": {"ufs-mediatek-mod.ko": {"sha256": MODULE.UFS_MODULE_SHA256}},
        "dma_window_bytes": 1 << 36,
        "source_binary_equivalence_verified": False,
        "physical_dma_route_verified": False,
        "installed_firmware_contract_verified": False,
        "physical_backend_enabled": False,
    }
    client = {
        "audit_complete": True,
        "saved_client": {
            "module_sha256": MODULE.UFS_MODULE_SHA256,
            "mcq_query": {"function_id": "0xc2000276", "selector": 1024},
            "offsets_are_runtime_addresses": False,
        },
        "installed_firmware_contract_verified": False,
        "physical_dma_route_verified": False,
        "physical_backend_enabled": False,
    }
    contract = {
        "passed": True,
        "saved_module_sha256": MODULE.UFS_MODULE_SHA256,
        "test_sources_unchanged": True,
        "physical_backend_enabled": False,
        "installed_firmware_contract_verified": False,
        "physical_dma_route_verified": False,
    }
    candidate = {
        "branch": "duchamp-bootstrap",
        "inputs": {"live_fdt_sha256": MODULE.FDT_SHA256},
        "outputs": {
            "candidate_sha256": MODULE.CANDIDATE_SHA256,
            "candidate_size": MODULE.CANDIDATE_BYTES,
        },
        "checks": {
            "payload_source_rebuild_phone": True,
            "payload_source_rebuild_qemu": True,
            "bootshim_host_entry_guard": True,
            "handoff_ready": True,
            "xnu_return_contract": True,
            "payload_preflight": True,
            "materializer": True,
            "return_slot": True,
            "embedded_payload_match_phone": True,
            "embedded_payload_match_qemu": True,
            "phone_elf_no_relocations": True,
            "phone_elf_no_unresolved_symbols": True,
            "phone_elf_indirect_branch_count": 1,
            "qemu_elf_no_relocations": True,
            "qemu_elf_no_unresolved_symbols": True,
            "qemu_elf_indirect_branch_count": 1,
            "qemu_xnu_jump": True,
            "qemu_white_pixels": 1,
            "avb_none_verified": True,
            "lz4_decompressed_match": True,
            "offline_gate_v18": True,
        },
        "safety": {
            "phone_write": False,
            "fastboot_used": False,
            "partition_access": False,
            "physical_mmio_executed": False,
            "physical_ufs_enabled": False,
            "phone_execution_authorized": False,
        },
    }
    candidate_receipt = {
        "bytes": MODULE.CANDIDATE_BYTES,
        "sha256": MODULE.CANDIDATE_SHA256,
    }
    return live, offline, saved, client, contract, candidate, candidate_receipt


class PhoneReadinessTests(unittest.TestCase):
    def test_valid_evidence_stays_blocked(self):
        result = MODULE.assess(*fixtures())
        self.assertTrue(result["evidence_validated"])
        self.assertEqual(result["assessment"], "blocked")
        self.assertTrue(result["diagnostic_candidate_prepared"])
        self.assertFalse(result["physical_phone_execution_authorized"])
        self.assertFalse(result["full_system_boot_ready"])
        self.assertFalse(result["physical_ufs_backend_authorized"])
        self.assertEqual(len(result["remaining_blockers"]), 5)

    def test_module_build_identity_is_exact(self):
        values = fixtures()
        values[0]["runtime"]["ufs"]["installed_module"]["gnu_build_id"] = "00" * 20
        with self.assertRaisesRegex(ValueError, "build ID differs"):
            MODULE.assess(*values)

    def test_direct_window_is_exact(self):
        values = fixtures()
        values[0]["dma"]["dt_direct_dma_windows"][0]["bytes"] = "0x80000000"
        with self.assertRaisesRegex(ValueError, "direct DMA window differs"):
            MODULE.assess(*values)

    def test_unreviewed_promotions_fail_closed(self):
        mutations = (
            ("firmware", "installed_ufs_sip_effect_contract_verified"),
            ("firmware", "physical_resource_ownership_verified"),
            ("dma", "physical_dma_bypass_verified"),
            ("dma", "coherency_verified"),
            ("dma", "xnu_dma_ready"),
        )
        for section, field in mutations:
            with self.subTest(field=field):
                values = fixtures()
                values[0][section][field] = True
                with self.assertRaisesRegex(ValueError, "unexpected"):
                    MODULE.assess(*values)

    def test_missing_offline_safety_fails(self):
        values = fixtures()
        values[1]["safety"]["phone_execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "unsafe offline-gate action"):
            MODULE.assess(*values)

    def test_candidate_image_must_match_manifest(self):
        values = fixtures()
        values[6]["sha256"] = "00" * 32
        with self.assertRaisesRegex(ValueError, "candidate image does not match"):
            MODULE.assess(*values)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            sentinel = output / "keep"
            sentinel.write_text("keep")
            command = [sys.executable, str(SCRIPT), str(output)]
            for option in ("--live-report", "--offline-gate", "--saved-audit",
                           "--client-audit", "--contract-model", "--candidate-manifest",
                           "--candidate-image"):
                command += [option, "missing"]
            process = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
