#!/usr/bin/env python3
"""Tests for the narrow Duchamp PRDT evidence interpreter."""

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("interpret-duchamp-prdt-observation.py")
SPEC = importlib.util.spec_from_file_location("prdt_interpreter", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    zero_fields = {
        name: 0
        for name in (
            "dma_to_phys_mismatches",
            "swiotlb_segments",
            "prdt_address_mismatches",
            "prdt_length_mismatches",
            "outside_bus_limit_segments",
            "translated_phys_invalid",
            "runtime_contract_changes",
            "rejected_calls",
            "hook_error_calls",
            "zero_length_segments",
            "unknown_direction_commands",
            "dma_end_overflows",
            "original_phys_end_overflows",
        )
    }
    after = {
        **zero_fields,
        "observation_version": 2,
        "coherent_snapshot": 1,
        "observation_complete": 1,
        "all_prdt_entries_match": 1,
        "all_segments_within_bus_limit": 1,
        "runtime_direct_dma_contract": 1,
        "all_dma_equals_original_without_swiotlb": 1,
        "runtime_bus_dma_limit": MODULE.EXPECTED_BUS_LIMIT,
        "segments": 8,
        "dma_to_phys_matches": 8,
        "above_4g_segments": 3,
    }
    safe_false = {
        name: False
        for name in (
            "boot_partition_modified",
            "cache_drop_requested",
            "dma_mapping_issued_by_observer",
            "firmware_call_issued_by_observer",
            "mmio_access_issued_by_observer",
            "partition_access",
            "reboot_requested",
            "selinux_policy_changed",
            "storage_command_issued_by_observer",
            "tracefs_control_changed",
        )
    }
    return {
        "report_version": 1,
        "passed": True,
        "errors": [],
        "target": {
            "device": "duchamp",
            "hardware": "mt6897",
            "kernel": MODULE.EXPECTED_KERNEL,
        },
        "artifact": {
            "sha256": MODULE.EXPECTED_MODULE_SHA256,
            "static_verification": "passed",
        },
        "preflight": {
            "root": True,
            "boot_completed": True,
            "installed_ufs_module_build_id": MODULE.EXPECTED_UFS_BUILD_ID,
            "installed_ufs_module_live": True,
            "orphan_tracefs_instance_absent": True,
        },
        "execution": {
            "boot_id_unchanged": True,
            "cleanup_clean": True,
            "kernel_log_comparable": True,
            "kernel_taint_unchanged": True,
            "module_loaded": True,
            "module_unloaded": True,
            "staged_file_removed": True,
            "new_kernel_fault_lines": [],
        },
        "observation": {
            "passed": True,
            "errors": [],
            "route_classification": MODULE.LEGACY_ROUTE,
            "linux_dma_direct_contract_pinned_during_snapshots": True,
            "physical_firewall_bypass_proven": False,
            "xnu_cache_ownership_proven": False,
            "read_workload_causality_proven": False,
            "after": after,
            "delta": {"commands": 4, "segments": 8},
        },
        "safety": {
            **safe_false,
            "approval_bound_to_module_sha256": MODULE.EXPECTED_MODULE_SHA256,
        },
    }


class InterpretPrdtTests(unittest.TestCase):
    def test_precise_claims_pass_without_raw_identity_promotion(self):
        result = MODULE.interpret_report(fixture())
        self.assertEqual(result["verdict"], "validated-limited-prdt-evidence")
        self.assertTrue(
            result["proven"][
                "inverse_dma_translation_returns_original_scatterlist_phys"
            ]
        )
        self.assertFalse(
            result["not_proven"]["raw_dma_address_equals_cpu_physical"]
        )

    def test_firewall_promotion_is_rejected(self):
        report = fixture()
        report["observation"]["physical_firewall_bypass_proven"] = True
        with self.assertRaisesRegex(ValueError, "firewall-bypass"):
            MODULE.interpret_report(report)

    def test_incomplete_inverse_translation_is_rejected(self):
        report = fixture()
        report["observation"]["after"]["dma_to_phys_matches"] = 7
        with self.assertRaisesRegex(ValueError, "accounting"):
            MODULE.interpret_report(report)

    def test_unsafe_action_is_rejected(self):
        report = fixture()
        report["safety"]["mmio_access_issued_by_observer"] = True
        with self.assertRaisesRegex(ValueError, "unsafe action"):
            MODULE.interpret_report(report)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "existing"
            output.mkdir()
            marker = output / "keep"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                MODULE.interpret_file(root / "missing.json", output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_wrong_input_hash_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "result.json"
            source.write_text(json.dumps(fixture()), encoding="utf-8")
            output = root / "output"
            with self.assertRaisesRegex(ValueError, "hash differs"):
                MODULE.interpret_file(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
