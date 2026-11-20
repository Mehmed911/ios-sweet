#!/usr/bin/env python3
"""Combine pinned Duchamp evidence into a fail-closed phone-readiness report.

This tool reads existing local JSON reports only.  A successful exit means the
evidence is internally consistent; it does not authorize phone execution,
physical MMIO, DMA, UFS, fastboot, or a partition write.
"""

import argparse
import hashlib
import json
from pathlib import Path


FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
UFS_MODULE_SHA256 = (
    "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493"
)
UFS_MODULE_BUILD_ID = "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
UFS_HWIRQS = [200, 209, 210, 211, 212, 213, 214, 215, 216]
CANDIDATE_SHA256 = "a83f0792ccd883c19a8225641b4e96090fb08673375e71fe93123e0dafddfaa8"
CANDIDATE_BYTES = 64 * 1024 * 1024
CURRENT_UFS_HCCAP = "0x55c7051f"
BL31_RELEASE = "lts-v2.8.6(release):2fbca47"
BL31_BUILT = "07:19:18, Dec 18 2024"
BL31_SOFTWARE_VERSION = "common_2.6.1(6897-1.2)"
BL31_SOFTWARE_BUILD = "Jun 8 2022(Jul 25 20:00:00 UTC 2023)"
TEE_A_BYTES = 5 * 1024 * 1024
TEE_A_SHA256 = "37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d"
ATF_BYTES = 0xE8E78
ATF_SHA256 = "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
UFS_SIP_REGION_SHA256 = {
    "smc_dispatch": "0f789f306af36bf5a7fac5ee968fe1b535433828d5b230f6b9012c5430b78095",
    "smc_handler_index": "3022972b23b33e57b1a50eb4f5d1f7325f9cdeeb8b4c76b02479a8aebfbfd729",
    "ufs_handler_entry": "e1aaf656abba8e5cb718d714bf3cd96945ce2f6b1504df9a9ba2ed8d4b2700de",
    "selector_decode": "073619861b1801f2a26c73ad1f1528c343d9c677c019e05cc8fd35c3dd819669",
    "refclk_branch": "eb22e149830d7e1b0411a83dbc40ba4e03c28271c5c11c3ebb4ce7c3fbf1d07c",
    "mtcmos_on_branch": "8b0c2734836f02ec6366c4dd840d48580319d9fcb6faeb753536dae5b895b544",
    "mtcmos_off_branch": "c87207b20336caf7850563a5df0104b225bdb0eafd443fdc437f792db3b20b92",
    "mcq_result_branch": "7f8da98d9d9b6e2e0c7aed8c54297a73e9909152d16bad19f45449a9bd3feac9",
    "known_selector_return": "4372938dd3785f100ddac14e1755828784fd2228c7530ad86f6719d22b3cd56d",
    "selector_jump_table": "18f0db7da1670e9d03602c5bb45e5b7d3fa639d42767a44cd102d58c24f8c878",
    "ufs_service_descriptor": "90dc59f5e8add8f9ff6c2c30ce80cfc31b5dabc90db8eb98eb769c989b7a740b",
    "mtcmos_control_0_entry": "f48b1f50ca0f1642ac9c4d45b197c642341bd5ef865e34e18d678fe763a014f4",
    "mtcmos_control_0_status": "0a73cc55a92e4ae8d1e95d910b4b622ab38f2715266972d45eeb71bfac7307f2",
    "mtcmos_control_1_entry": "acfc763e6ba2db9813070b3b13f9669ca00bd81a0078bc78e823c7da418eeb98",
    "mtcmos_control_1_status": "7d4fdf6abc221fa9edd40394b567ae0555b5ad547a50fbf3d8c1e2bf1be617d6",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def value(mapping, *path):
    current = mapping
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise ValueError("missing evidence field: " + ".".join(path))
        current = current[key]
    return current


def validate_live(report):
    require(value(report, "report_version") == 2, "unsupported live report version")
    require(value(report, "result", "passed") is True, "live report did not pass")
    require(
        value(report, "fdt", "reference_sha256") == FDT_SHA256,
        "live report reference DTB differs",
    )
    require(
        value(report, "fdt", "critical_topology_matches_reference") is True,
        "live critical topology differs",
    )
    require(value(report, "fdt", "added_nodes") == [], "live FDT added nodes")
    require(value(report, "fdt", "removed_nodes") == [], "live FDT removed nodes")

    timer = value(report, "runtime", "timer")
    require(timer.get("android_runtime_delivery_observed") is True, "Android timer delivery missing")
    require(timer.get("xnu_phone_delivery_observed") is False, "unexpected XNU timer promotion")
    require(timer.get("clocksource") == "arch_sys_counter", "unexpected clocksource")
    require(timer.get("clockevent") == "arch_sys_timer", "unexpected clockevent")
    require(timer.get("gic_hwirq") == 27, "unexpected timer HWIRQ")
    require(isinstance(timer.get("total_delta"), int) and timer["total_delta"] > 0,
            "timer counter did not advance")

    ufs = value(report, "runtime", "ufs")
    require(ufs.get("android_runtime_delivery_observed") is True, "Android UFS delivery missing")
    require(ufs.get("xnu_phone_delivery_observed") is False, "unexpected XNU UFS promotion")
    require(ufs.get("driver") == "/sys/bus/platform/drivers/ufshcd-mtk",
            "unexpected UFS driver")
    require(ufs.get("expected_gic_hwirqs") == UFS_HWIRQS, "unexpected UFS HWIRQs")
    require(isinstance(ufs.get("total_delta"), int) and ufs["total_delta"] > 0,
            "UFS counters did not advance")
    module = value(ufs, "installed_module")
    saved_module = value(module, "saved_vendor_module")
    require(module.get("name") == "ufs_mediatek_mod" and module.get("state") == "Live",
            "installed UFS module identity differs")
    require(module.get("gnu_build_id") == UFS_MODULE_BUILD_ID,
            "installed UFS module build ID differs")
    require(saved_module.get("sha256") == UFS_MODULE_SHA256,
            "saved UFS module hash differs")
    require(saved_module.get("gnu_build_id") == UFS_MODULE_BUILD_ID,
            "saved UFS module build ID differs")
    require(saved_module.get("build_id_match_verified") is True,
            "installed/saved UFS build ID match missing")
    require(saved_module.get("source_commit_match_verified") is False,
            "unexpected UFS source-build promotion")
    require(module.get("local_source_commit_match_verified") is False,
            "unexpected local source-build promotion")

    runtime_contract = value(ufs, "runtime_contract")
    hccap = value(runtime_contract, "hccap")
    require(
        hccap.get("status") == "not-exposed-in-capture"
        and hccap.get("value") is None
        and hccap.get("candidate_entries") == [],
        "unexpected runtime HCCAP promotion",
    )
    for key in ("streaming_dma_mask_bits", "coherent_dma_mask_bits"):
        item = value(runtime_contract, key)
        require(
            item == {"status": "unavailable", "value": None},
            "unexpected runtime DMA-mask promotion: " + key,
        )
    for key in ("dma_ops", "iommu_fwspec", "iommu_domain"):
        item = value(runtime_contract, key)
        require(
            item == {"status": "not-captured", "value": None},
            "unexpected runtime DMA-contract promotion: " + key,
        )
    swiotlb = value(runtime_contract, "swiotlb_pool")
    require(
        swiotlb == {
            "status": "not-captured",
            "value": None,
            "cmdline_policy": "noforce",
        },
        "unexpected runtime SWIOTLB promotion",
    )
    require(
        value(runtime_contract, "cache_ownership")
        == {"status": "unverified", "value": None},
        "unexpected runtime cache-ownership promotion",
    )

    firmware = value(report, "firmware")
    require(firmware.get("installed_scmi_identity_observed") is True,
            "installed SCMI identity missing")
    require(firmware.get("installed_ufs_client_binary_identity_verified") is True,
            "installed UFS client binary identity missing")
    for key in (
        "installed_ufs_sip_abi_verified",
        "installed_ufs_sip_effect_contract_verified",
        "xnu_firmware_abi_verified",
        "physical_resource_ownership_verified",
    ):
        require(firmware.get(key) is False, "unexpected firmware promotion: " + key)

    dma = value(report, "dma")
    windows = dma.get("dt_direct_dma_windows")
    require(
        windows == [{
            "path": "/soc",
            "child_bus_start": "0x0",
            "parent_bus_start": "0x0",
            "bytes": "0x1000000000",
            "identity": True,
        }],
        "direct DMA window differs",
    )
    require(dma.get("dt_iommu_binding_declared") is False, "unexpected DT IOMMU binding")
    require(dma.get("linux_sysfs_iommu_group_attached") is False,
            "unexpected Linux IOMMU group")
    require(dma.get("linux_iommu_supplier_links") == [], "unexpected IOMMU supplier")
    for key in ("physical_dma_bypass_verified", "coherency_verified", "xnu_dma_ready"):
        require(dma.get(key) is False, "unexpected DMA promotion: " + key)

    safety = value(report, "safety")
    require(safety.get("offline_analysis_only") is True, "live report was not offline-only")
    require(safety.get("read_only_inputs") is True, "live report inputs were not read-only")
    for key in ("adb_access_by_this_tool", "mmio_access", "phone_write", "partition_access"):
        require(safety.get(key) is False, "unsafe live-report action: " + key)
    return {
        "android_timer_irq_delivery": True,
        "android_ufs_irq_delivery": True,
        "critical_live_fdt_topology": True,
        "direct_identity_dma_window_bytes": 1 << 36,
        "linux_ufs_iommu_attachment_observed": False,
        "installed_ufs_module_binary_identity": True,
        "runtime_hccap_status": hccap["status"],
        "runtime_dma_mask_status": "unavailable",
        "runtime_swiotlb_pool_status": swiotlb["status"],
    }


def validate_shell_runtime(report):
    require(report.get("passed") is True, "shell runtime report did not pass")
    target = value(report, "target")
    require(
        target.get("device") == "duchamp" and target.get("hardware") == "mt6897",
        "shell runtime target differs",
    )
    require(target.get("ufs_boot_controller_matches_saved_dtb") is True,
            "shell runtime UFS boot controller differs")
    require(report.get("reference_dtb_sha256") == FDT_SHA256,
            "shell runtime reference DTB differs")

    timer = value(report, "runtime", "timer")
    require(timer.get("gic_hwirq") == 27, "shell runtime timer HWIRQ differs")
    require(isinstance(timer.get("total_delta"), int) and timer["total_delta"] > 0,
            "shell runtime timer did not advance")
    ufs = value(report, "runtime", "ufs")
    require(ufs.get("expected_gic_hwirqs") == UFS_HWIRQS,
            "shell runtime expected UFS HWIRQs differ")
    require(ufs.get("observed_gic_hwirqs") == UFS_HWIRQS,
            "shell runtime observed UFS HWIRQs differ")
    require(isinstance(ufs.get("total_delta"), int) and ufs["total_delta"] > 0,
            "shell runtime UFS counters did not advance")

    firmware = value(report, "firmware")
    require(firmware.get("cpuidle_driver") == "psci_idle",
            "shell runtime cpuidle driver differs")
    require(firmware.get("scmi_driver") == "/sys/bus/platform/drivers/arm-scmi",
            "shell runtime SCMI driver differs")
    module = value(firmware, "installed_ufs_module")
    require(module.get("name") == "ufs_mediatek_mod" and module.get("state") == "Live",
            "shell runtime UFS module differs")
    bl31 = value(firmware, "installed_bl31_identity")
    require(
        bl31.get("status") == "observed"
        and bl31.get("release") == BL31_RELEASE
        and bl31.get("built") == BL31_BUILT
        and bl31.get("software_version") == BL31_SOFTWARE_VERSION,
        "installed BL31 identity differs",
    )

    root_probes = value(report, "root_access_probes")
    for key in ("identity", "cmdline", "iomem", "ufs_sysfs_list",
                "ufs_capabilities_list", "debugfs_root_list", "atf_log_head",
                "ufs_recursive_list", "ufs_proc_debug", "kernel_log_ufs",
                "ufs_scsi_can_queue",
                "ufs_scsi_nr_hw_queues", "ufs_scsi_sg_tablesize",
                "ufs_scsi_cmd_per_lun"):
        require(value(root_probes, key).get("status") == "readable",
                "required root read missing: " + key)
    require(value(root_probes, "ufs_iommu_group").get("status") == "unavailable",
            "unexpected UFS IOMMU-group promotion")

    runtime_contract = value(report, "runtime_ufs_contract")
    hccap = value(runtime_contract, "hccap")
    require(
        hccap.get("status") == "observed-via-proc-debug"
        and hccap.get("value") == CURRENT_UFS_HCCAP
        and hccap.get("candidate_entries") == []
        and hccap.get("sysfs_capability_entries") == [
            "clock_scaling", "write_booster"
        ]
        and hccap.get("supports_64_bit_addressing") is True,
        "shell runtime HCCAP differs",
    )
    require(
        value(hccap, "recursive_interface_inventory") == {
            "status": "captured",
            "bounded_lines": 1200,
            "hccap_candidate_entries": [],
            "dma_mask_candidate_entries": [],
        },
        "unexpected recursive UFS interface inventory",
    )
    require(
        value(hccap, "proc_debug") == {
            "status": "observed",
            "source": "/proc/ufs_debug",
            "effective_host_capabilities": CURRENT_UFS_HCCAP,
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
        "bounded UFS proc debug differs",
    )
    for key in ("streaming_dma_mask_bits", "coherent_dma_mask_bits"):
        item = value(runtime_contract, key)
        require(item.get("status") == "unavailable" and item.get("value") is None,
                "unexpected shell runtime DMA-mask promotion: " + key)
    require(
        value(runtime_contract, "swiotlb_pool") == {
            "status": "not-captured",
            "value": None,
            "cmdline_policy": {"status": "specified", "value": "noforce"},
        },
        "unexpected shell runtime SWIOTLB promotion",
    )
    require(value(runtime_contract, "cache_ownership") == {
        "status": "unverified", "value": None
    }, "unexpected shell runtime cache-ownership promotion")

    expected_scsi_queue = {
        "can_queue": 63,
        "nr_hw_queues": 8,
        "sg_tablesize": 128,
        "cmd_per_lun": 31,
    }
    scsi_queue = value(runtime_contract, "scsi_host_queue")
    for key, expected in expected_scsi_queue.items():
        item = value(scsi_queue, key)
        require(
            item.get("status") == "readable"
            and item.get("readable") is True
            and item.get("value") == expected,
            "shell runtime SCSI queue differs: " + key,
        )
    bounded_kernel_log = value(runtime_contract, "bounded_kernel_log_ufs")
    require(
        bounded_kernel_log.get("status") == "readable"
        and bounded_kernel_log.get("readable") is True
        and isinstance(bounded_kernel_log.get("stdout_bytes"), int)
        and bounded_kernel_log["stdout_bytes"] > 0,
        "bounded UFS kernel log capture missing",
    )

    claims = value(report, "claims")
    require(claims.get("installed_bl31_identity_observed") is True,
            "BL31 identity observation missing")
    require(claims.get("android_ufs_multiqueue_observed") is True,
            "Android UFS multiqueue observation missing")
    require(claims.get("android_ufs_hccap_observed") is True,
            "Android UFS HCCAP observation missing")
    for key in ("installed_bl31_ufs_effect_contract_verified",
                "xnu_phone_delivery_observed",
                "gic_or_firmware_ownership_verified_for_xnu",
                "ufs_dma_or_iommu_route_verified"):
        require(claims.get(key) is False, "unexpected shell runtime promotion: " + key)

    safety = value(report, "safety")
    require(safety.get("root_requested") is True,
            "root read-only capture was not identified")
    require(safety.get("root_commands_allowlisted") is True,
            "root reads were not allowlisted")
    for key in ("device_writes", "fastboot_access", "partition_access", "mmio_access"):
        require(safety.get(key) is False, "unsafe shell runtime action: " + key)
    return {
        "current_android_timer_irq_delta": timer["total_delta"],
        "current_android_ufs_irq_delta": ufs["total_delta"],
        "installed_bl31_identity_observed": True,
        "installed_bl31_release": bl31["release"],
        "installed_bl31_built": bl31["built"],
        "installed_bl31_runtime_identity_observed": True,
        "current_ufs_iommu_group_status": "unavailable",
        "current_runtime_hccap_status": hccap["status"],
        "current_runtime_hccap": hccap["value"],
        "current_runtime_hccap_supports_64_bit_addressing": True,
        "current_runtime_dma_mask_status": "unavailable",
        "current_android_ufs_multiqueue_observed": True,
        "current_android_ufs_scsi_queue": expected_scsi_queue,
    }


def validate_firmware_binary(report):
    require(report.get("report_version") == 1,
            "unsupported firmware binary report version")
    require(report.get("passed") is True, "firmware binary report did not pass")
    require(value(report, "input") == {
        "bytes": TEE_A_BYTES,
        "sha256": TEE_A_SHA256,
    }, "captured tee_a receipt differs")

    entry = value(report, "atf_entry")
    require(entry.get("outer_magic") == "0x58881688",
            "captured tee_a outer magic differs")
    require(entry.get("inner_magic") == "0x58891689",
            "captured tee_a inner magic differs")
    require(entry.get("name") == "atf", "captured tee_a entry differs")
    require(entry.get("declared_payload_bytes") == 0xE8E78,
            "captured tee_a payload size differs")
    require(entry.get("header_payload_offset") == 0x200,
            "captured tee_a payload offset differs")
    require(entry.get("payload_start") == 0x200,
            "captured tee_a payload start differs")
    require(entry.get("payload_end_exclusive") == 0xE9078,
            "captured tee_a payload end differs")
    require(entry.get("alignment_bytes") == 0x10,
            "captured tee_a alignment differs")
    require(entry.get("alignment_padding_bytes") == 8,
            "captured tee_a alignment padding differs")
    require(entry.get("next_entry_offset") == 0xE9080,
            "captured tee_a next entry offset differs")
    require(entry.get("next_entry_name") == "cert1",
            "captured tee_a next entry differs")

    identity = value(report, "bl31_binary_identity")
    require(identity.get("status") == "observed-in-atf-entry",
            "captured BL31 identity status differs")
    require(identity.get("release") == BL31_RELEASE,
            "captured BL31 release differs")
    require(identity.get("built") == BL31_BUILT,
            "captured BL31 build time differs")
    require(identity.get("software_version") == BL31_SOFTWARE_VERSION,
            "captured BL31 software version differs")
    require(identity.get("software_build") == BL31_SOFTWARE_BUILD,
            "captured BL31 software build differs")
    require(identity.get("matches_bounded_runtime_log_identity") is True,
            "captured BL31/runtime identity match missing")
    offsets = identity.get("string_offsets")
    require(isinstance(offsets, dict), "captured BL31 string offsets missing")
    for key in ("release", "built", "software", "platform",
                "software_built", "software_build_host_time"):
        require(isinstance(offsets.get(key), int)
                and 0x200 <= offsets[key] < 0xE9078,
                "captured BL31 string offset differs: " + key)

    claims = value(report, "claims")
    require(claims.get("captured_tee_a_binary_identity_verified") is True,
            "captured tee_a identity verification missing")
    require(claims.get("bl31_runtime_identity_string_match_verified") is True,
            "captured BL31/runtime identity verification missing")
    for key in ("bl31_public_source_equivalence_verified",
                "bl31_ufs_sip_effect_contract_verified",
                "physical_resource_ownership_verified",
                "xnu_physical_ufs_ready"):
        require(claims.get(key) is False,
                "unexpected firmware binary promotion: " + key)

    safety = value(report, "safety")
    require(safety.get("local_file_only") is True,
            "firmware inspector was not local-file-only")
    for key in ("adb_access_by_this_tool", "phone_write", "partition_write",
                "fastboot_access", "mmio_access", "smc_execution"):
        require(safety.get(key) is False,
                "unsafe firmware binary action: " + key)
    return {
        "captured_active_tee_a_sha256": TEE_A_SHA256,
        "captured_active_tee_a_bl31_identity_match": True,
        "installed_bl31_public_source_equivalence_verified": False,
        "installed_bl31_ufs_effect_contract_verified": False,
    }


def validate_firmware_sip_audit(report):
    require(report.get("report_version") == 1,
            "unsupported firmware SiP audit version")
    require(report.get("passed") is True, "firmware SiP audit did not pass")
    require(value(report, "tee_a") == {
        "bytes": TEE_A_BYTES,
        "sha256": TEE_A_SHA256,
    }, "firmware SiP tee_a receipt differs")
    require(value(report, "atf") == {
        "bytes": ATF_BYTES,
        "sha256": ATF_SHA256,
    }, "firmware SiP atf receipt differs")

    service = value(report, "service")
    require(service.get("name") == "MTK_SIP_KERNEL_UFS_CONTROL",
            "firmware UFS service name differs")
    require(service.get("descriptor_offset") == 0x66020,
            "firmware UFS descriptor offset differs")
    require(service.get("handler_address") == "0x48845008",
            "firmware UFS handler address differs")
    require(service.get("fast32_function_id") == "0x82000276"
            and service.get("fast64_function_id") == "0xc2000276",
            "firmware UFS function IDs differ")
    require(service.get("static_registration_index") == -1,
            "firmware UFS registration sentinel differs")
    require(service.get("dispatcher_target") == "0x4882b634",
            "firmware UFS dispatcher target differs")

    selectors = value(report, "selectors")
    require(value(selectors, "refclk") == {
        "value": 8,
        "target": "0x48845170",
        "pre_post_stage_checks_present": True,
    }, "firmware REFCLK selector path differs")
    require(value(selectors, "mtcmos") == {
        "value": 512,
        "target": "0x488451ec",
        "body_present": True,
        "on_helper_target": "0x4883a078",
        "off_helper_target": "0x4883a40c",
        "followup_helper_target": "0x4883a078",
    }, "firmware MTCMOS selector path differs")
    require(value(selectors, "mcq") == {
        "value": 1024,
        "target": "0x48845098",
        "state_load_and_result_store_present": True,
    }, "firmware MCQ selector path differs")
    require(value(report, "mtcmos_mmio") == {
        "unlock_register": "0x1c001000",
        "unlock_value": "0x0b160001",
        "control_registers": ["0x1c001e10", "0x1c001e14"],
        "polled_status_bits": [30, 31],
        "captured_bl31_direct_mmio_paths_present": True,
        "safe_xnu_direct_readback_authorized": False,
    }, "firmware MTCMOS MMIO path differs")

    regions = value(report, "pinned_regions")
    require(set(regions) == set(UFS_SIP_REGION_SHA256),
            "firmware SiP pinned-region set differs")
    for name, expected_hash in UFS_SIP_REGION_SHA256.items():
        require(value(regions, name).get("sha256") == expected_hash,
                "firmware SiP region hash differs: " + name)

    claims = value(report, "claims")
    for key in ("captured_bl31_ufs_service_descriptor_verified",
                "saved_client_function_id_dispatch_verified",
                "saved_refclk_selector_dispatch_verified",
                "saved_mtcmos_selector_dispatch_verified",
                "saved_mcq_selector_dispatch_verified",
                "mtcmos_body_present_in_captured_binary",
                "known_selector_common_zero_return_present",
                "captured_bl31_mtcmos_mmio_paths_verified"):
        require(claims.get(key) is True,
                "firmware SiP static proof missing: " + key)
    for key in ("zero_reply_proves_physical_effect",
                "direct_xnu_mtcmos_mmio_authorized",
                "runtime_smc_return_effect_contract_verified",
                "physical_resource_ownership_verified",
                "xnu_physical_ufs_ready"):
        require(claims.get(key) is False,
                "unexpected firmware SiP promotion: " + key)

    safety = value(report, "safety")
    require(safety.get("local_file_only") is True,
            "firmware SiP audit was not local-file-only")
    for key in ("firmware_executed", "smc_execution", "mmio_access",
                "adb_access_by_this_tool", "phone_write", "partition_write",
                "fastboot_access"):
        require(safety.get(key) is False,
                "unsafe firmware SiP audit action: " + key)
    return {
        "captured_bl31_ufs_service_dispatch_verified": True,
        "captured_bl31_refclk_mtcmos_mcq_paths_verified": True,
        "captured_bl31_mtcmos_body_present": True,
        "captured_bl31_known_selector_common_zero_return": True,
        "captured_bl31_mtcmos_mmio_paths_verified": True,
        "captured_bl31_mtcmos_control_registers": [
            "0x1c001e10", "0x1c001e14"
        ],
        "xnu_direct_mtcmos_readback_authorized": False,
        "firmware_zero_reply_proves_physical_effect": False,
        "firmware_runtime_effect_contract_verified": False,
    }


def validate_dma_ownership_audit(report):
    require(report.get("report_version") == 2,
            "unsupported DMA ownership audit version")
    require(report.get("audit_passed") is True,
            "DMA ownership audit did not pass")
    require(report.get("target") == {"device": "duchamp", "soc": "mt6897"},
            "DMA ownership target differs")

    masks = value(report, "dma_masks")
    require(masks.get("effective_streaming_mask") == "0xffffffffffffffff"
            and masks.get("effective_streaming_mask_bits") == 64,
            "live streaming DMA mask differs")
    require(masks.get("effective_coherent_mask") == "0xffffffffffffffff"
            and masks.get("effective_coherent_mask_bits") == 64,
            "live coherent DMA mask differs")
    require(masks.get("bus_dma_limit") == "0x0000000fffffffff"
            and masks.get("bus_dma_limit_bits") == 36,
            "live bus DMA limit differs")
    require(masks.get("exact_masks_proven") is True,
            "exact live DMA masks were not proven")
    require(masks.get("dma_coherent") is False,
            "unexpected coherent UFS DMA classification")

    route = value(report, "iommu_route")
    require(route.get("runtime_dma_ops_state_observed") is True
            and route.get("runtime_dma_ops_present") is False
            and route.get("runtime_device_dma_ops_present") is False,
            "runtime DMA ops state differs")
    require(route.get("linux_dma_api_path") == "generic dma-direct",
            "runtime Linux DMA path differs")
    require(route.get("runtime_iommu_fwspec_state_observed") is True
            and route.get("runtime_iommu_fwspec_present") is False,
            "runtime IOMMU fwspec state differs")
    require(route.get("runtime_iommu_domain_state_observed") is True
            and route.get("runtime_iommu_domain_present") is False,
            "runtime IOMMU domain state differs")
    require(route.get("linux_iommu_attachment_absent_at_observation") is True,
            "Linux IOMMU attachment was not excluded")
    require(route.get("device_swiotlb_pool_present") is True,
            "device SWIOTLB pool state differs")
    require(route.get("swiotlb_transfer_observed") is False,
            "unexpected SWIOTLB transfer promotion")
    require(route.get("physical_iommu_bypass_verified") is False,
            "unexpected physical IOMMU bypass promotion")

    verdict = value(report, "verdict")
    require(verdict.get("physical_xnu_ufs_ready") is False,
            "unexpected physical XNU UFS readiness")
    require(verdict.get("physical_backend_enabled") is False,
            "physical UFS backend was enabled")

    safety = value(report, "safety")
    require(safety.get("audit_execution_offline") is True,
            "DMA ownership audit was not offline")
    require(safety.get("runtime_probe_evidence_included") is True,
            "DMA ownership audit lacks runtime probe evidence")
    require(safety.get("probe_module_loaded_and_unloaded") is True
            and safety.get("probe_cleanup_verified") is True,
            "DMA probe cleanup was not verified")
    for key in (
        "partition_access",
        "boot_partition_modified",
        "storage_command_by_probe",
        "dma_mapping_by_probe",
        "iommu_mapping_or_attachment_by_probe",
        "smc_execution_by_probe",
        "mmio_access_by_probe",
    ):
        require(safety.get(key) is False, "unsafe DMA probe action: " + key)

    return {
        "runtime_dma_masks_proven": True,
        "runtime_streaming_dma_mask_bits": 64,
        "runtime_coherent_dma_mask_bits": 64,
        "runtime_bus_dma_limit_bits": 36,
        "runtime_linux_dma_api_path": "generic dma-direct",
        "runtime_linux_iommu_attachment_observed": False,
        "runtime_device_swiotlb_pool_present": True,
        "runtime_swiotlb_transfer_observed": False,
        "runtime_dma_cache_ownership_verified": False,
        "physical_dma_bypass_verified": False,
    }


def validate_offline_gate(report):
    require(report.get("passed") is True, "offline gate did not pass")
    require(report.get("inputs_unchanged") is True, "offline gate inputs changed")
    require(value(report, "input_sha256", "fdt") == FDT_SHA256,
            "offline gate DTB differs")
    safety = value(report, "safety")
    for key in ("physical_device_access", "mmio_access", "flash_or_partition_write",
                "phone_execution_authorized"):
        require(safety.get(key) is False, "unsafe offline-gate action: " + key)
    blockers = value(report, "remaining_physical_blockers")
    require(blockers.get("installed_firmware_contract") == "unverified",
            "unexpected offline firmware promotion")
    require(blockers.get("physical_ufs_backend") == "disabled",
            "physical UFS backend was enabled")
    require(blockers.get("ufs_topckgen_physical_backend") == "disabled",
            "physical topckgen backend was enabled")
    return True


def validate_saved_audit(report):
    require(report.get("audit_complete") is True, "saved UFS audit incomplete")
    require(value(report, "input_sha256", "fdt") == FDT_SHA256,
            "saved UFS audit DTB differs")
    require(value(report, "modules", "ufs-mediatek-mod.ko", "sha256") == UFS_MODULE_SHA256,
            "saved UFS audit module differs")
    require(report.get("dma_window_bytes") == 1 << 36, "saved DMA window differs")
    for key in ("source_binary_equivalence_verified", "physical_dma_route_verified",
                "installed_firmware_contract_verified", "physical_backend_enabled"):
        require(report.get(key) is False, "unexpected saved-audit promotion: " + key)
    return True


def validate_client_audit(report):
    require(report.get("audit_complete") is True, "firmware client audit incomplete")
    client = value(report, "saved_client")
    require(client.get("module_sha256") == UFS_MODULE_SHA256,
            "firmware client module differs")
    query = value(client, "mcq_query")
    require(query.get("function_id") == "0xc2000276" and query.get("selector") == 1024,
            "firmware client MCQ request differs")
    require(client.get("offsets_are_runtime_addresses") is False,
            "static offsets were promoted to runtime addresses")
    for key in ("installed_firmware_contract_verified", "physical_dma_route_verified",
                "physical_backend_enabled"):
        require(report.get(key) is False, "unexpected client-audit promotion: " + key)
    return True


def validate_contract_model(report):
    require(report.get("passed") is True, "saved contract model did not pass")
    require(report.get("saved_module_sha256") == UFS_MODULE_SHA256,
            "contract model module differs")
    require(report.get("test_sources_unchanged") is True,
            "contract model sources changed")
    for key in ("physical_backend_enabled", "installed_firmware_contract_verified",
                "physical_dma_route_verified"):
        require(report.get(key) is False, "unexpected contract-model promotion: " + key)
    return True


def validate_candidate(manifest, image_receipt):
    require(manifest.get("branch") == "duchamp-bootstrap", "candidate branch differs")
    require(value(manifest, "inputs", "live_fdt_sha256") == FDT_SHA256,
            "candidate DTB differs")
    outputs = value(manifest, "outputs")
    require(outputs.get("candidate_sha256") == CANDIDATE_SHA256,
            "candidate manifest hash differs")
    require(outputs.get("candidate_size") == CANDIDATE_BYTES,
            "candidate manifest size differs")
    require(image_receipt == {"bytes": CANDIDATE_BYTES, "sha256": CANDIDATE_SHA256},
            "candidate image does not match its pinned manifest")
    checks = value(manifest, "checks")
    for key in (
        "payload_source_rebuild_phone",
        "payload_source_rebuild_qemu",
        "bootshim_host_entry_guard",
        "handoff_ready",
        "xnu_return_contract",
        "payload_preflight",
        "materializer",
        "return_slot",
        "embedded_payload_match_phone",
        "embedded_payload_match_qemu",
        "phone_elf_no_relocations",
        "phone_elf_no_unresolved_symbols",
        "qemu_elf_no_relocations",
        "qemu_elf_no_unresolved_symbols",
        "qemu_xnu_jump",
        "avb_none_verified",
        "lz4_decompressed_match",
        "offline_gate_v18",
    ):
        require(checks.get(key) is True, "candidate check missing: " + key)
    require(checks.get("phone_elf_indirect_branch_count") == 1,
            "candidate phone branch count differs")
    require(checks.get("qemu_elf_indirect_branch_count") == 1,
            "candidate QEMU branch count differs")
    require(isinstance(checks.get("qemu_white_pixels"), int)
            and checks["qemu_white_pixels"] > 0, "candidate QEMU XNU pixels missing")
    safety = value(manifest, "safety")
    for key in ("phone_write", "fastboot_used", "partition_access",
                "physical_mmio_executed", "physical_ufs_enabled",
                "phone_execution_authorized"):
        require(safety.get(key) is False, "unsafe candidate action: " + key)
    return True


def assess(live, offline, saved, client, contract, candidate, candidate_receipt,
           shell_runtime, firmware_binary, firmware_sip_audit,
           dma_ownership_audit):
    observed = validate_live(live)
    observed.update(validate_shell_runtime(shell_runtime))
    observed.update(validate_firmware_binary(firmware_binary))
    observed.update(validate_firmware_sip_audit(firmware_sip_audit))
    observed.update(validate_dma_ownership_audit(dma_ownership_audit))
    validate_offline_gate(offline)
    validate_saved_audit(saved)
    validate_client_audit(client)
    validate_contract_model(contract)
    validate_candidate(candidate, candidate_receipt)
    blockers = [
        {
            "id": "xnu_phone_timer_irq_delivery",
            "verified": False,
            "needed": "bounded diagnostic execution proving XNU timer and IRQ delivery",
        },
        {
            "id": "installed_firmware_effect_contract",
            "verified": False,
            "needed": "runtime proof of each requested UFS effect and secure ownership; the captured handler shares a zero-return exit and its exact source remains unmatched",
        },
        {
            "id": "physical_resource_ownership",
            "verified": False,
            "needed": "exclusive GIC/UFS/PHY/clock/reset ownership for XNU",
        },
        {
            "id": "runtime_ufs_dma_contract",
            "verified": False,
            "needed": "physical firewall/translation behavior, actual bounce requirements and non-coherent cache ownership; masks, Linux DMA ops and IOMMU state are now observed",
        },
        {
            "id": "xnu_physical_ufs_backend",
            "verified": False,
            "needed": "reviewed backend that remains disabled until all earlier contracts pass",
        },
    ]
    return {
        "evidence_validated": True,
        "safe_offline_stage_complete": True,
        "assessment": "blocked",
        "diagnostic_candidate_prepared": True,
        "physical_phone_execution_authorized": False,
        "full_system_boot_ready": False,
        "physical_ufs_backend_authorized": False,
        "observed": observed,
        "remaining_blockers": blockers,
        "next_safe_work": [
            "document the physical firewall and non-coherent cache-maintenance contract before any DMA experiment",
            "design a readback-based effect verifier for REFCLK/MTCMOS; do not accept the captured handler's common zero return as success",
            "find exact source for captured vendor BL31 release 2fbca47; the public upstream lts-v2.8.6 commit differs",
            "keep the MT6897 physical UFS provider disabled",
        ],
        "safety": {
            "local_json_inputs_only": True,
            "adb_access": False,
            "phone_write": False,
            "fastboot_access": False,
            "partition_access": False,
            "mmio_access": False,
            "smc_execution": False,
            "read_only_partition_capture_used_as_local_evidence": True,
        },
        "scope": (
            "evidence consistency and fail-closed readiness assessment only; "
            "not authorization for a phone trial"
        ),
    }


def read_report(path):
    raw = path.read_bytes()
    if len(raw) > 64 * 1024 * 1024:
        raise ValueError("JSON evidence file is too large: " + str(path))
    report = json.loads(raw)
    if not isinstance(report, dict):
        raise ValueError("JSON evidence root is not an object: " + str(path))
    return report, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def file_receipt(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            digest.update(block)
    return {"bytes": size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--live-report", type=Path, required=True)
    parser.add_argument("--offline-gate", type=Path, required=True)
    parser.add_argument("--saved-audit", type=Path, required=True)
    parser.add_argument("--client-audit", type=Path, required=True)
    parser.add_argument("--contract-model", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-image", type=Path, required=True)
    parser.add_argument("--shell-runtime", type=Path, required=True)
    parser.add_argument("--firmware-binary-report", type=Path, required=True)
    parser.add_argument("--firmware-sip-audit", type=Path, required=True)
    parser.add_argument("--dma-ownership-audit", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    paths = {
        "live_report": args.live_report,
        "offline_gate": args.offline_gate,
        "saved_audit": args.saved_audit,
        "client_audit": args.client_audit,
        "contract_model": args.contract_model,
        "candidate_manifest": args.candidate_manifest,
        "shell_runtime": args.shell_runtime,
        "firmware_binary_report": args.firmware_binary_report,
        "firmware_sip_audit": args.firmware_sip_audit,
        "dma_ownership_audit": args.dma_ownership_audit,
    }
    try:
        loaded = {name: read_report(path.resolve()) for name, path in paths.items()}
        reports = {name: item[0] for name, item in loaded.items()}
        candidate_receipt = file_receipt(args.candidate_image.resolve())
        result = assess(
            reports["live_report"],
            reports["offline_gate"],
            reports["saved_audit"],
            reports["client_audit"],
            reports["contract_model"],
            reports["candidate_manifest"],
            candidate_receipt,
            reports["shell_runtime"],
            reports["firmware_binary_report"],
            reports["firmware_sip_audit"],
            reports["dma_ownership_audit"],
        )
        receipts = {name: item[1] for name, item in loaded.items()}
        receipts["candidate_image"] = candidate_receipt
        for name, path in paths.items():
            require(read_report(path.resolve())[1] == receipts[name],
                    "evidence changed during assessment: " + name)
        require(file_receipt(args.candidate_image.resolve()) == candidate_receipt,
                "candidate image changed during assessment")
        result["input_receipts"] = receipts
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, "phone readiness assessment failed: " + str(error) + "\n")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
