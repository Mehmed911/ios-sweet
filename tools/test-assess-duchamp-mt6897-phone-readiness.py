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
        "report_version": 2,
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
                "runtime_contract": {
                    "hccap": {
                        "status": "not-exposed-in-capture",
                        "value": None,
                        "sysfs_capability_entries": [
                            "clock_scaling",
                            "write_booster",
                        ],
                        "debugfs_entries": [],
                        "candidate_entries": [],
                    },
                    "streaming_dma_mask_bits": {
                        "status": "unavailable",
                        "value": None,
                    },
                    "coherent_dma_mask_bits": {
                        "status": "unavailable",
                        "value": None,
                    },
                    "dma_ops": {"status": "not-captured", "value": None},
                    "iommu_fwspec": {"status": "not-captured", "value": None},
                    "iommu_domain": {"status": "not-captured", "value": None},
                    "swiotlb_pool": {
                        "status": "not-captured",
                        "value": None,
                        "cmdline_policy": "noforce",
                    },
                    "cache_ownership": {"status": "unverified", "value": None},
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
    shell_runtime = {
        "passed": True,
        "target": {
            "device": "duchamp",
            "hardware": "mt6897",
            "ufs_boot_controller_matches_saved_dtb": True,
        },
        "reference_dtb_sha256": MODULE.FDT_SHA256,
        "runtime": {
            "timer": {"gic_hwirq": 27, "total_delta": 10},
            "ufs": {
                "expected_gic_hwirqs": MODULE.UFS_HWIRQS,
                "observed_gic_hwirqs": MODULE.UFS_HWIRQS,
                "total_delta": 2,
            },
        },
        "firmware": {
            "cpuidle_driver": "psci_idle",
            "scmi_driver": "/sys/bus/platform/drivers/arm-scmi",
            "installed_ufs_module": {
                "name": "ufs_mediatek_mod",
                "state": "Live",
            },
            "installed_bl31_identity": {
                "status": "observed",
                "release": MODULE.BL31_RELEASE,
                "built": MODULE.BL31_BUILT,
                "software_version": MODULE.BL31_SOFTWARE_VERSION,
            },
        },
        "root_access_probes": {
            key: {"status": "readable"}
            for key in (
                "identity", "cmdline", "iomem", "ufs_sysfs_list",
                "ufs_capabilities_list", "debugfs_root_list", "atf_log_head",
                "ufs_recursive_list", "ufs_proc_debug", "kernel_log_ufs",
                "ufs_scsi_can_queue",
                "ufs_scsi_nr_hw_queues", "ufs_scsi_sg_tablesize",
                "ufs_scsi_cmd_per_lun",
            )
        },
        "runtime_ufs_contract": {
            "hccap": {
                "status": "observed-via-proc-debug",
                "value": MODULE.CURRENT_UFS_HCCAP,
                "candidate_entries": [],
                "sysfs_capability_entries": ["clock_scaling", "write_booster"],
                "supports_64_bit_addressing": True,
                "recursive_interface_inventory": {
                    "status": "captured",
                    "bounded_lines": 1200,
                    "hccap_candidate_entries": [],
                    "dma_mask_candidate_entries": [],
                },
                "proc_debug": {
                    "status": "observed",
                    "source": "/proc/ufs_debug",
                    "effective_host_capabilities": MODULE.CURRENT_UFS_HCCAP,
                    "hba_caps": "0x000001c5",
                    "mtk_caps": "0x000006c0",
                    "host_version": "0x400",
                    "device_version": "0x400",
                    "supports_64_bit_addressing": True,
                    "mcq_supported": True,
                    "mcq_enabled": True,
                    "nr_hw_queues": 8,
                    "nutrs": 64,
                    "device_queue_depth": 64,
                    "effective_dma_mask_bits": None,
                },
            },
            "streaming_dma_mask_bits": {"status": "unavailable", "value": None},
            "coherent_dma_mask_bits": {"status": "unavailable", "value": None},
            "swiotlb_pool": {
                "status": "not-captured",
                "value": None,
                "cmdline_policy": {"status": "specified", "value": "noforce"},
            },
            "cache_ownership": {"status": "unverified", "value": None},
            "scsi_host_queue": {
                "can_queue": {
                    "status": "readable", "readable": True, "value": 63,
                },
                "nr_hw_queues": {
                    "status": "readable", "readable": True, "value": 8,
                },
                "sg_tablesize": {
                    "status": "readable", "readable": True, "value": 128,
                },
                "cmd_per_lun": {
                    "status": "readable", "readable": True, "value": 31,
                },
            },
            "bounded_kernel_log_ufs": {
                "status": "readable", "readable": True, "stdout_bytes": 470,
            },
        },
        "claims": {
            "android_ufs_multiqueue_observed": True,
            "android_ufs_hccap_observed": True,
            "installed_bl31_identity_observed": True,
            "installed_bl31_ufs_effect_contract_verified": False,
            "xnu_phone_delivery_observed": False,
            "gic_or_firmware_ownership_verified_for_xnu": False,
            "ufs_dma_or_iommu_route_verified": False,
        },
        "safety": {
            "root_requested": True,
            "root_commands_allowlisted": True,
            "device_writes": False,
            "fastboot_access": False,
            "partition_access": False,
            "mmio_access": False,
        },
    }
    shell_runtime["root_access_probes"]["ufs_iommu_group"] = {
        "status": "unavailable"
    }
    firmware_binary = {
        "report_version": 1,
        "passed": True,
        "input": {
            "bytes": MODULE.TEE_A_BYTES,
            "sha256": MODULE.TEE_A_SHA256,
        },
        "atf_entry": {
            "outer_magic": "0x58881688",
            "inner_magic": "0x58891689",
            "name": "atf",
            "declared_payload_bytes": 0xE8E78,
            "header_payload_offset": 0x200,
            "payload_start": 0x200,
            "payload_end_exclusive": 0xE9078,
            "alignment_bytes": 0x10,
            "alignment_padding_bytes": 8,
            "next_entry_offset": 0xE9080,
            "next_entry_name": "cert1",
        },
        "bl31_binary_identity": {
            "status": "observed-in-atf-entry",
            "release": MODULE.BL31_RELEASE,
            "built": MODULE.BL31_BUILT,
            "software_version": MODULE.BL31_SOFTWARE_VERSION,
            "software_build": MODULE.BL31_SOFTWARE_BUILD,
            "string_offsets": {
                "release": 0x53204,
                "built": 0x531E6,
                "software": 0x61867,
                "platform": 0x61874,
                "software_built": 0x618B6,
                "software_build_host_time": 0x618C1,
            },
            "matches_bounded_runtime_log_identity": True,
        },
        "claims": {
            "captured_tee_a_binary_identity_verified": True,
            "bl31_runtime_identity_string_match_verified": True,
            "bl31_public_source_equivalence_verified": False,
            "bl31_ufs_sip_effect_contract_verified": False,
            "physical_resource_ownership_verified": False,
            "xnu_physical_ufs_ready": False,
        },
        "safety": {
            "local_file_only": True,
            "adb_access_by_this_tool": False,
            "phone_write": False,
            "partition_write": False,
            "fastboot_access": False,
            "mmio_access": False,
            "smc_execution": False,
        },
    }
    firmware_sip_audit = {
        "report_version": 1,
        "passed": True,
        "tee_a": {"bytes": MODULE.TEE_A_BYTES, "sha256": MODULE.TEE_A_SHA256},
        "atf": {"bytes": MODULE.ATF_BYTES, "sha256": MODULE.ATF_SHA256},
        "service": {
            "name": "MTK_SIP_KERNEL_UFS_CONTROL",
            "descriptor_offset": 0x66020,
            "handler_address": "0x48845008",
            "fast32_function_id": "0x82000276",
            "fast64_function_id": "0xc2000276",
            "static_registration_index": -1,
            "dispatcher_target": "0x4882b634",
        },
        "selectors": {
            "refclk": {
                "value": 8,
                "target": "0x48845170",
                "pre_post_stage_checks_present": True,
            },
            "mtcmos": {
                "value": 512,
                "target": "0x488451ec",
                "body_present": True,
                "on_helper_target": "0x4883a078",
                "off_helper_target": "0x4883a40c",
                "followup_helper_target": "0x4883a078",
            },
            "mcq": {
                "value": 1024,
                "target": "0x48845098",
                "state_load_and_result_store_present": True,
            },
        },
        "mtcmos_mmio": {
            "unlock_register": "0x1c001000",
            "unlock_value": "0x0b160001",
            "control_registers": ["0x1c001e10", "0x1c001e14"],
            "polled_status_bits": [30, 31],
            "captured_bl31_direct_mmio_paths_present": True,
            "safe_xnu_direct_readback_authorized": False,
        },
        "pinned_regions": {
            name: {"offset": 1, "bytes": 1, "sha256": digest}
            for name, digest in MODULE.UFS_SIP_REGION_SHA256.items()
        },
        "claims": {
            "captured_bl31_ufs_service_descriptor_verified": True,
            "saved_client_function_id_dispatch_verified": True,
            "saved_refclk_selector_dispatch_verified": True,
            "saved_mtcmos_selector_dispatch_verified": True,
            "saved_mcq_selector_dispatch_verified": True,
            "mtcmos_body_present_in_captured_binary": True,
            "known_selector_common_zero_return_present": True,
            "captured_bl31_mtcmos_mmio_paths_verified": True,
            "zero_reply_proves_physical_effect": False,
            "direct_xnu_mtcmos_mmio_authorized": False,
            "runtime_smc_return_effect_contract_verified": False,
            "physical_resource_ownership_verified": False,
            "xnu_physical_ufs_ready": False,
        },
        "safety": {
            "local_file_only": True,
            "firmware_executed": False,
            "smc_execution": False,
            "mmio_access": False,
            "adb_access_by_this_tool": False,
            "phone_write": False,
            "partition_write": False,
            "fastboot_access": False,
        },
    }
    dma_ownership_audit = {
        "report_version": 2,
        "audit_passed": True,
        "target": {"device": "duchamp", "soc": "mt6897"},
        "dma_masks": {
            "effective_streaming_mask": "0xffffffffffffffff",
            "effective_streaming_mask_bits": 64,
            "effective_coherent_mask": "0xffffffffffffffff",
            "effective_coherent_mask_bits": 64,
            "bus_dma_limit": "0x0000000fffffffff",
            "bus_dma_limit_bits": 36,
            "exact_masks_proven": True,
            "dma_coherent": False,
        },
        "iommu_route": {
            "runtime_dma_ops_state_observed": True,
            "runtime_dma_ops_present": False,
            "runtime_device_dma_ops_present": False,
            "linux_dma_api_path": "generic dma-direct",
            "runtime_iommu_fwspec_state_observed": True,
            "runtime_iommu_fwspec_present": False,
            "runtime_iommu_domain_state_observed": True,
            "runtime_iommu_domain_present": False,
            "linux_iommu_attachment_absent_at_observation": True,
            "device_swiotlb_pool_present": True,
            "swiotlb_transfer_observed": False,
            "physical_iommu_bypass_verified": False,
        },
        "verdict": {
            "physical_xnu_ufs_ready": False,
            "physical_backend_enabled": False,
        },
        "safety": {
            "audit_execution_offline": True,
            "runtime_probe_evidence_included": True,
            "probe_module_loaded_and_unloaded": True,
            "probe_cleanup_verified": True,
            "partition_access": False,
            "boot_partition_modified": False,
            "storage_command_by_probe": False,
            "dma_mapping_by_probe": False,
            "iommu_mapping_or_attachment_by_probe": False,
            "smc_execution_by_probe": False,
            "mmio_access_by_probe": False,
        },
    }
    return (
        live, offline, saved, client, contract, candidate, candidate_receipt,
        shell_runtime, firmware_binary, firmware_sip_audit, dma_ownership_audit,
    )


class PhoneReadinessTests(unittest.TestCase):
    def test_valid_evidence_stays_blocked(self):
        result = MODULE.assess(*fixtures())
        self.assertTrue(result["evidence_validated"])
        self.assertEqual(result["assessment"], "blocked")
        self.assertTrue(result["diagnostic_candidate_prepared"])
        self.assertFalse(result["physical_phone_execution_authorized"])
        self.assertFalse(result["full_system_boot_ready"])
        self.assertFalse(result["physical_ufs_backend_authorized"])
        self.assertTrue(result["observed"]["runtime_dma_masks_proven"])
        self.assertEqual(
            result["observed"]["runtime_linux_dma_api_path"],
            "generic dma-direct",
        )
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

    def test_dma_ownership_masks_are_exact(self):
        values = fixtures()
        values[10]["dma_masks"]["bus_dma_limit_bits"] = 64
        with self.assertRaisesRegex(ValueError, "bus DMA limit differs"):
            MODULE.assess(*values)

    def test_dma_ownership_does_not_promote_physical_bypass(self):
        values = fixtures()
        values[10]["iommu_route"]["physical_iommu_bypass_verified"] = True
        with self.assertRaisesRegex(ValueError, "physical IOMMU bypass"):
            MODULE.assess(*values)

    def test_dma_probe_cleanup_is_required(self):
        values = fixtures()
        values[10]["safety"]["probe_cleanup_verified"] = False
        with self.assertRaisesRegex(ValueError, "cleanup was not verified"):
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

    def test_unreviewed_runtime_contract_promotions_fail_closed(self):
        mutations = (
            ("hccap", "status", "readable"),
            ("streaming_dma_mask_bits", "value", 64),
            ("coherent_dma_mask_bits", "value", 64),
            ("dma_ops", "status", "direct"),
            ("iommu_domain", "status", "absent"),
            ("swiotlb_pool", "status", "inactive"),
            ("cache_ownership", "status", "coherent"),
        )
        for section, field, replacement in mutations:
            with self.subTest(section=section, field=field):
                values = fixtures()
                values[0]["runtime"]["ufs"]["runtime_contract"][section][field] = replacement
                with self.assertRaisesRegex(ValueError, "unexpected runtime"):
                    MODULE.assess(*values)

    def test_current_bl31_identity_is_exact_but_effects_stay_blocked(self):
        values = fixtures()
        values[7]["firmware"]["installed_bl31_identity"]["release"] = "other"
        with self.assertRaisesRegex(ValueError, "BL31 identity differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[7]["claims"]["installed_bl31_ufs_effect_contract_verified"] = True
        with self.assertRaisesRegex(ValueError, "unexpected shell runtime promotion"):
            MODULE.assess(*values)

    def test_current_root_capture_safety_is_fail_closed(self):
        values = fixtures()
        values[7]["safety"]["device_writes"] = True
        with self.assertRaisesRegex(ValueError, "unsafe shell runtime action"):
            MODULE.assess(*values)

        values = fixtures()
        values[7]["runtime_ufs_contract"]["scsi_host_queue"][
            "nr_hw_queues"
        ]["value"] = 7
        with self.assertRaisesRegex(ValueError, "SCSI queue differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[7]["runtime_ufs_contract"]["hccap"][
            "recursive_interface_inventory"
        ]["hccap_candidate_entries"] = ["caps"]
        with self.assertRaisesRegex(ValueError, "recursive UFS interface"):
            MODULE.assess(*values)

        values = fixtures()
        values[7]["runtime_ufs_contract"]["hccap"]["value"] = "0x00000000"
        with self.assertRaisesRegex(ValueError, "HCCAP differs"):
            MODULE.assess(*values)

    def test_captured_firmware_identity_is_exact_but_effects_stay_blocked(self):
        values = fixtures()
        values[8]["input"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(ValueError, "tee_a receipt differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[8]["bl31_binary_identity"]["release"] = "other"
        with self.assertRaisesRegex(ValueError, "BL31 release differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[8]["claims"]["bl31_ufs_sip_effect_contract_verified"] = True
        with self.assertRaisesRegex(ValueError, "unexpected firmware binary promotion"):
            MODULE.assess(*values)

    def test_firmware_inspector_safety_is_fail_closed(self):
        values = fixtures()
        values[8]["safety"]["partition_write"] = True
        with self.assertRaisesRegex(ValueError, "unsafe firmware binary action"):
            MODULE.assess(*values)

    def test_firmware_sip_paths_are_exact_but_runtime_effects_stay_blocked(self):
        values = fixtures()
        values[9]["selectors"]["mtcmos"]["target"] = "0x0"
        with self.assertRaisesRegex(ValueError, "MTCMOS selector path differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[9]["claims"]["runtime_smc_return_effect_contract_verified"] = True
        with self.assertRaisesRegex(ValueError, "unexpected firmware SiP promotion"):
            MODULE.assess(*values)

        values = fixtures()
        values[9]["pinned_regions"]["smc_dispatch"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(ValueError, "region hash differs"):
            MODULE.assess(*values)

        values = fixtures()
        values[9]["mtcmos_mmio"]["safe_xnu_direct_readback_authorized"] = True
        with self.assertRaisesRegex(ValueError, "MTCMOS MMIO path differs"):
            MODULE.assess(*values)

    def test_firmware_sip_safety_is_fail_closed(self):
        values = fixtures()
        values[9]["safety"]["smc_execution"] = True
        with self.assertRaisesRegex(ValueError, "unsafe firmware SiP audit action"):
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
                           "--candidate-image", "--shell-runtime",
                           "--firmware-binary-report", "--firmware-sip-audit",
                           "--dma-ownership-audit"):
                command += [option, "missing"]
            process = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
