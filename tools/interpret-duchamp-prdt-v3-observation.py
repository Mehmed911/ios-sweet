#!/usr/bin/env python3
"""Validate and normalize the pinned Duchamp PRDT v3 phone result."""

import argparse
import hashlib
import json
import os
from pathlib import Path


RESULT_SHA256 = "0fc223d4474535f269766c268b74cab05b2028501ee234f3bab5eb1782053bc9"
ARTIFACT_SHA256 = "49196936b7d6ca78f485b35fc3d7ba0407f3027ec9a70b6bae9658f1c1862f96"
EXPECTED_KERNEL = "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407"
EXPECTED_RANGE_SIZE = 0x1000000000
EXPECTED_BUS_LIMIT = EXPECTED_RANGE_SIZE - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(path):
    raw = path.read_bytes()
    require(sha256(raw) == RESULT_SHA256, "PRDT v3 result hash differs")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("PRDT v3 result is not valid UTF-8 JSON") from error

    require(result.get("report_version") == 1, "unexpected result version")
    require(result.get("passed") is True, "live PRDT v3 run did not pass")
    require(
        result.get("artifact", {}).get("sha256") == ARTIFACT_SHA256,
        "observer artifact hash differs",
    )
    target = result.get("target", {})
    require(target.get("device") == "duchamp", "target device differs")
    require(target.get("hardware") == "mt6897", "target hardware differs")
    require(target.get("kernel") == EXPECTED_KERNEL, "target kernel differs")

    execution = result.get("execution", {})
    for field in (
        "module_loaded",
        "module_unloaded",
        "staged_file_removed",
        "cleanup_clean",
        "boot_id_unchanged",
        "kernel_taint_unchanged",
        "kernel_log_comparable",
    ):
        require(execution.get(field) is True, "cleanup field failed: " + field)
    require(not execution.get("new_kernel_fault_lines"), "new kernel fault found")

    observation = result.get("observation", {})
    require(observation.get("passed") is True, "observation did not pass")
    require(not observation.get("errors"), "observation contains errors")
    require(
        observation.get("route_classification")
        == "raw-dma-equals-original-pa-no-swiotlb-under-live-identity-map",
        "unexpected live DMA route",
    )
    require(
        observation.get("raw_dma_address_equals_original_phys_proven") is True,
        "raw DMA-to-PA identity was not proven",
    )
    require(
        observation.get("forward_and_inverse_translation_proven") is True,
        "DMA translations were not proven",
    )
    require(observation.get("swiotlb_bounce_observed") is False,
            "SWIOTLB bounce was observed")
    require(observation.get("swiotlb_force_bounce") is False,
            "SWIOTLB force-bounce was enabled")
    require(observation.get("physical_firewall_bypass_proven") is False,
            "result overclaims firewall ownership")
    require(observation.get("xnu_cache_ownership_proven") is False,
            "result overclaims XNU cache ownership")

    after = observation.get("after", {})
    require(after.get("dma_range_count") == 1, "live DMA map count differs")
    require(after.get("dma_range_terminated") == 1,
            "live DMA map is not terminated")
    require(after.get("dma_range_cpu_start") == 0,
            "live CPU range start differs")
    require(after.get("dma_range_dma_start") == 0,
            "live DMA range start differs")
    require(after.get("dma_range_size") == EXPECTED_RANGE_SIZE,
            "live DMA range size differs")
    require(after.get("dma_range_offset") == 0,
            "live DMA range offset differs")
    require(after.get("runtime_bus_dma_limit") == EXPECTED_BUS_LIMIT,
            "live bus DMA limit differs")
    for field in (
        "runtime_direct_dma_contract",
        "dma_range_identity",
        "dma_range_stable",
        "all_prdt_entries_match",
        "all_raw_dma_equals_original_phys",
        "all_phys_to_dma_matches",
        "all_dma_to_phys_matches",
        "no_swiotlb_observed",
        "observed_direct_identity_route",
    ):
        require(after.get(field) == 1, "live proof flag differs: " + field)
    segments = after.get("segments")
    require(isinstance(segments, int) and segments > 0,
            "no live segments were observed")
    for field in (
        "raw_dma_phys_matches",
        "phys_to_dma_matches",
        "dma_to_phys_matches",
    ):
        require(after.get(field) == segments, field + " does not cover all segments")
    for field in (
        "raw_dma_phys_mismatches",
        "phys_to_dma_mismatches",
        "dma_to_phys_mismatches",
        "swiotlb_segments",
        "rejected_calls",
        "runtime_contract_changes",
    ):
        require(after.get(field) == 0, field + " is non-zero")
    require(after.get("swiotlb_pool_present") == 1,
            "device SWIOTLB pointer disappeared")
    require(after.get("swiotlb_pool_active") == 0,
            "device SWIOTLB pool is active")
    require(after.get("swiotlb_force_bounce") == 0,
            "device SWIOTLB force-bounce changed")

    delta = observation.get("delta", {})
    require(delta.get("segments", 0) > 0, "bounded workload observed no segments")
    require(delta.get("read_commands", 0) > 0,
            "bounded workload observed no reads")
    require(delta.get("raw_dma_phys_matches") == delta.get("segments"),
            "bounded segment identity accounting differs")

    safety = result.get("safety", {})
    for field in (
        "boot_partition_modified",
        "partition_access",
        "reboot_requested",
        "selinux_policy_changed",
        "tracefs_control_changed",
        "mmio_access_issued_by_observer",
        "firmware_call_issued_by_observer",
        "dma_mapping_issued_by_observer",
        "storage_command_issued_by_observer",
    ):
        require(safety.get(field) is False, "unsafe result flag: " + field)

    return {
        "report_version": 1,
        "verdict": "validated-live-direct-dma-evidence",
        "target": {
            "device": "duchamp",
            "soc": "mt6897",
            "engine": "ufs",
            "kernel": EXPECTED_KERNEL,
        },
        "proven": {
            "live_dma_range_entries_captured": True,
            "live_dma_range_is_identity": True,
            "dma_range_cpu_start": 0,
            "dma_range_dma_start": 0,
            "dma_range_bytes": EXPECTED_RANGE_SIZE,
            "raw_dma_equals_cpu_pa_for_all_observed_segments": True,
            "forward_and_inverse_translation_for_all_observed_segments": True,
            "observed_segments_total": segments,
            "observed_segments_in_bounded_window": delta["segments"],
            "swiotlb_pool_inactive": True,
            "swiotlb_force_bounce_false": True,
            "no_swiotlb_segments_observed": True,
            "cleanup_complete": True,
        },
        "not_proven": {
            "physical_firewall_or_secure_firmware_delegation": False,
            "xnu_cache_maintenance_ownership": False,
            "clock_reset_phy_regulator_ownership": False,
            "all_future_allocations_follow_observed_workload": False,
        },
        "inputs": {
            "phone_result_sha256": RESULT_SHA256,
            "observer_artifact_sha256": ARTIFACT_SHA256,
        },
        "scope": (
            "live Linux UFS address-route proof for the observed workload; "
            "not XNU physical-controller ownership"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    report = validate(args.result.resolve(strict=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
