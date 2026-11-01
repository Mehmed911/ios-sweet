#!/usr/bin/env python3
"""Validate and narrowly interpret the approved Duchamp PRDT observation.

This is local-file-only.  It deliberately distinguishes inverse DMA
translation from raw DMA/CPU-physical numeric identity.
"""

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_RESULT_SHA256 = (
    "81f1210b67a659103d3c4c863dd6baafd85e39dfb77132b4382efab1a91de5d4"
)
EXPECTED_MODULE_SHA256 = (
    "fb5b1a887bced8e4b0fbf498ebafc21d4856b4f57bbf2795f1d469bd8c9984c3"
)
EXPECTED_UFS_BUILD_ID = "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
EXPECTED_KERNEL = "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407"
EXPECTED_BUS_LIMIT = (1 << 36) - 1
LEGACY_ROUTE = "dma-equals-original-phys-no-swiotlb-under-pinned-contract"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def interpret_report(report):
    require(report.get("report_version") == 1, "unsupported report version")
    require(report.get("passed") is True, "live observation did not pass")
    require(report.get("errors") == [], "live runner reported errors")

    target = report.get("target", {})
    require(target.get("device") == "duchamp", "unexpected device")
    require(target.get("hardware") == "mt6897", "unexpected hardware")
    require(target.get("kernel") == EXPECTED_KERNEL, "unexpected kernel")

    artifact = report.get("artifact", {})
    require(
        artifact.get("sha256") == EXPECTED_MODULE_SHA256,
        "observer artifact hash differs",
    )
    require(
        artifact.get("static_verification") == "passed",
        "observer static verification missing",
    )

    preflight = report.get("preflight", {})
    require(preflight.get("root") is True, "root preflight missing")
    require(preflight.get("boot_completed") is True, "Android boot incomplete")
    require(
        preflight.get("installed_ufs_module_build_id") == EXPECTED_UFS_BUILD_ID,
        "installed UFS Build ID differs",
    )
    require(
        preflight.get("installed_ufs_module_live") is True,
        "installed UFS module was not live",
    )
    require(
        preflight.get("orphan_tracefs_instance_absent") is True,
        "stale tracefs instance was present",
    )

    execution = report.get("execution", {})
    for field in (
        "boot_id_unchanged",
        "cleanup_clean",
        "kernel_log_comparable",
        "kernel_taint_unchanged",
        "module_loaded",
        "module_unloaded",
        "staged_file_removed",
    ):
        require(execution.get(field) is True, "execution check failed: " + field)
    require(
        execution.get("new_kernel_fault_lines") == [],
        "new kernel fault line observed",
    )

    observation = report.get("observation", {})
    require(observation.get("passed") is True, "observation did not pass")
    require(observation.get("errors") == [], "observation reported errors")
    require(
        observation.get("route_classification") == LEGACY_ROUTE,
        "unexpected historical route classification",
    )
    require(
        observation.get("linux_dma_direct_contract_pinned_during_snapshots")
        is True,
        "dma-direct snapshot contract missing",
    )
    require(
        observation.get("physical_firewall_bypass_proven") is False,
        "unexpected firewall-bypass promotion",
    )
    require(
        observation.get("xnu_cache_ownership_proven") is False,
        "unexpected XNU cache-ownership promotion",
    )
    require(
        observation.get("read_workload_causality_proven") is False,
        "unexpected workload-causality promotion",
    )

    after = observation.get("after", {})
    delta = observation.get("delta", {})
    require(after.get("observation_version") == 2, "unexpected observer version")
    for field in (
        "coherent_snapshot",
        "observation_complete",
        "all_prdt_entries_match",
        "all_segments_within_bus_limit",
        "runtime_direct_dma_contract",
        "all_dma_equals_original_without_swiotlb",
    ):
        require(after.get(field) == 1, "observer summary failed: " + field)
    require(
        after.get("runtime_bus_dma_limit") == EXPECTED_BUS_LIMIT,
        "unexpected live bus DMA limit",
    )
    for field in (
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
    ):
        require(after.get(field) == 0, "non-zero observer counter: " + field)
    require(
        after.get("segments") == after.get("dma_to_phys_matches"),
        "inverse DMA translation accounting is incomplete",
    )
    require(delta.get("commands", 0) > 0, "no workload-window command")
    require(delta.get("segments", 0) > 0, "no workload-window segment")

    safety = report.get("safety", {})
    require(
        safety.get("approval_bound_to_module_sha256") == EXPECTED_MODULE_SHA256,
        "approval was not bound to the exact module",
    )
    for field in (
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
    ):
        require(safety.get(field) is False, "unsafe action reported: " + field)

    return {
        "report_version": 1,
        "verdict": "validated-limited-prdt-evidence",
        "proven": {
            "prdt_matches_mapped_scatterlist": True,
            "inverse_dma_translation_returns_original_scatterlist_phys": True,
            "no_swiotlb_observed_in_sample": True,
            "all_observed_extents_within_36bit_bus_limit": True,
            "dma_direct_no_iommu_contract_pinned_at_snapshots": True,
            "observer_cleanup_verified": True,
        },
        "not_proven": {
            "raw_dma_address_equals_cpu_physical": False,
            "live_dma_range_map_is_identity": False,
            "physical_firewall_bypass": False,
            "xnu_cache_ownership": False,
            "xnu_gic_or_ufs_ownership": False,
            "xnu_physical_ufs_ready": False,
            "read_workload_caused_every_observed_command": False,
        },
        "observation": {
            "commands_delta": delta["commands"],
            "segments_delta": delta["segments"],
            "segments_above_4g_total": after["above_4g_segments"],
            "bus_dma_limit": after["runtime_bus_dma_limit"],
            "historical_route_label": observation["route_classification"],
        },
        "safety": {
            "local_file_only": True,
            "adb_access": False,
            "phone_write": False,
            "mmio_access": False,
            "smc_execution": False,
            "partition_access": False,
        },
    }


def interpret_file(result_path, output_dir):
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    raw = result_path.read_bytes()
    digest = sha256(raw)
    require(digest == EXPECTED_RESULT_SHA256, "live-result hash differs")
    report = json.loads(raw.decode("utf-8"))
    interpretation = interpret_report(report)
    interpretation["input_receipt"] = {
        "name": result_path.name,
        "bytes": len(raw),
        "sha256": digest,
        "observer_module_sha256": EXPECTED_MODULE_SHA256,
        "installed_ufs_module_build_id": EXPECTED_UFS_BUILD_ID,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "interpretation.json").write_text(
        json.dumps(interpretation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return interpretation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = interpret_file(args.result.resolve(), args.output.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
