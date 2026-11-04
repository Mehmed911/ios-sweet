#!/usr/bin/env python3
"""Run one approved, bounded Duchamp UFS PRDT v3 observation.

The proven v2 lifecycle supplies target pinning, artifact verification,
staging, cleanup and fault checks. This wrapper replaces only the module
identity and the strict v3 report parser/evaluator. It still never flashes,
reboots, touches a partition, issues storage I/O, or changes SELinux.
"""

import importlib.util
from pathlib import Path
import re


BASE_SCRIPT = Path(__file__).with_name("capture-duchamp-ufs-prdt-observer.py")
APPROVAL_PREFIX = "I_APPROVE_DUCHAMP_PRDT_V3_"
MODULE_NAME = "duchamp_ufs_prdt_observer_v3"
SYSFS_ATTRIBUTE = (
    "/sys/devices/platform/soc/112b0000.ufshci/"
    "sweet_ufs_prdt_observation_v3"
)
EXPECTED_DMA_RANGE_SIZE = 0x0000001000000000
U64_MASK = (1 << 64) - 1

DECIMAL_FIELDS = {
    "observation_version",
    "root_read_only",
    "coherent_snapshot",
    "runtime_direct_dma_contract",
    "dma_range_count",
    "dma_range_terminated",
    "dma_range_identity",
    "dma_range_stable",
    "swiotlb_pool_present",
    "swiotlb_pool_active",
    "swiotlb_force_bounce",
    "hook_calls",
    "target_calls",
    "rejected_calls",
    "commands",
    "segments",
    "read_commands",
    "write_commands",
    "bidirectional_commands",
    "unknown_direction_commands",
    "hook_error_calls",
    "zero_length_segments",
    "dma_end_overflows",
    "translated_phys_invalid",
    "original_phys_end_overflows",
    "expected_dma_invalid",
    "prdt_address_mismatches",
    "prdt_length_mismatches",
    "swiotlb_segments",
    "raw_dma_phys_matches",
    "raw_dma_phys_mismatches",
    "phys_to_dma_matches",
    "phys_to_dma_mismatches",
    "dma_to_phys_matches",
    "dma_to_phys_mismatches",
    "above_4g_segments",
    "outside_bus_limit_segments",
    "runtime_contract_changes",
    "max_segment_length",
    "observation_complete",
    "all_prdt_entries_match",
    "all_raw_dma_equals_original_phys",
    "all_phys_to_dma_matches",
    "all_dma_to_phys_matches",
    "no_swiotlb_observed",
    "observed_direct_identity_route",
}
HEX_FIELDS = {
    "dma_range_cpu_start",
    "dma_range_dma_start",
    "dma_range_size",
    "dma_range_offset",
    "min_dma_address",
    "max_dma_end",
    "min_original_phys",
    "max_original_phys_end",
    "runtime_bus_dma_limit",
}
FLAG_FIELDS = {
    "root_read_only",
    "coherent_snapshot",
    "runtime_direct_dma_contract",
    "dma_range_terminated",
    "dma_range_identity",
    "dma_range_stable",
    "swiotlb_pool_present",
    "swiotlb_pool_active",
    "swiotlb_force_bounce",
    "observation_complete",
    "all_prdt_entries_match",
    "all_raw_dma_equals_original_phys",
    "all_phys_to_dma_matches",
    "all_dma_to_phys_matches",
    "no_swiotlb_observed",
    "observed_direct_identity_route",
}
COUNTER_FIELDS = {
    "hook_calls",
    "target_calls",
    "rejected_calls",
    "commands",
    "segments",
    "read_commands",
    "write_commands",
    "bidirectional_commands",
    "unknown_direction_commands",
    "hook_error_calls",
    "zero_length_segments",
    "dma_end_overflows",
    "translated_phys_invalid",
    "original_phys_end_overflows",
    "expected_dma_invalid",
    "prdt_address_mismatches",
    "prdt_length_mismatches",
    "swiotlb_segments",
    "raw_dma_phys_matches",
    "raw_dma_phys_mismatches",
    "phys_to_dma_matches",
    "phys_to_dma_mismatches",
    "dma_to_phys_matches",
    "dma_to_phys_mismatches",
    "above_4g_segments",
    "outside_bus_limit_segments",
    "runtime_contract_changes",
    "max_segment_length",
}
ZERO_REQUIRED_FIELDS = {
    "rejected_calls",
    "hook_error_calls",
    "unknown_direction_commands",
    "zero_length_segments",
    "dma_end_overflows",
    "translated_phys_invalid",
    "original_phys_end_overflows",
    "expected_dma_invalid",
    "prdt_address_mismatches",
    "prdt_length_mismatches",
    "swiotlb_segments",
    "raw_dma_phys_mismatches",
    "phys_to_dma_mismatches",
    "dma_to_phys_mismatches",
    "outside_bus_limit_segments",
    "runtime_contract_changes",
}


def load_base():
    spec = importlib.util.spec_from_file_location("capture_prdt_v2", BASE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_observation(text):
    values = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.count("=") != 1:
            raise ValueError("malformed PRDT v3 observation line")
        key, raw = line.split("=", 1)
        if key in values:
            raise ValueError("duplicate PRDT v3 observation field: " + key)
        if key in DECIMAL_FIELDS:
            if not raw.isdecimal():
                raise ValueError("invalid decimal PRDT v3 field: " + key)
            values[key] = int(raw, 10)
        elif key in HEX_FIELDS:
            if not re.fullmatch(r"0x[0-9a-fA-F]{16}", raw):
                raise ValueError("invalid hexadecimal PRDT v3 field: " + key)
            values[key] = int(raw, 16)
        else:
            raise ValueError("unexpected PRDT v3 observation field: " + key)

    missing = sorted((DECIMAL_FIELDS | HEX_FIELDS) - set(values))
    if missing:
        raise ValueError("missing PRDT v3 observation fields: " + ", ".join(missing))
    if values["observation_version"] != 3:
        raise ValueError("unexpected PRDT v3 observation version")
    for field in sorted(FLAG_FIELDS):
        if values[field] not in (0, 1):
            raise ValueError("invalid PRDT v3 observation flag: " + field)
    if values["root_read_only"] != 1:
        raise ValueError("PRDT v3 report is not root-read-only")
    if values["dma_range_count"] != 1 or values["dma_range_terminated"] != 1:
        raise ValueError("live DMA range map is not one terminated entry")
    if not values["dma_range_size"]:
        raise ValueError("live DMA range is empty")
    cpu_end = values["dma_range_cpu_start"] + values["dma_range_size"] - 1
    dma_end = values["dma_range_dma_start"] + values["dma_range_size"] - 1
    if cpu_end > U64_MASK or dma_end > U64_MASK:
        raise ValueError("live DMA range overflows 64 bits")
    expected_offset = (
        values["dma_range_cpu_start"] - values["dma_range_dma_start"]
    ) & U64_MASK
    if values["dma_range_offset"] != expected_offset:
        raise ValueError("live DMA range offset is inconsistent")
    expected_identity = int(
        values["dma_range_cpu_start"] == values["dma_range_dma_start"]
        and values["dma_range_offset"] == 0
    )
    if values["dma_range_identity"] != expected_identity:
        raise ValueError("live DMA range identity flag is inconsistent")
    if values["runtime_bus_dma_limit"] != BASE.EXPECTED_BUS_DMA_LIMIT:
        raise ValueError("runtime UFS bus DMA limit changed")
    if values["hook_calls"] < values["target_calls"]:
        raise ValueError("target calls exceed all hook calls")
    if values["target_calls"] != values["commands"] + values["rejected_calls"]:
        raise ValueError("target-call accounting is inconsistent")
    directions = sum(
        values[field]
        for field in (
            "read_commands",
            "write_commands",
            "bidirectional_commands",
            "unknown_direction_commands",
        )
    )
    if directions != values["commands"]:
        raise ValueError("command direction accounting is inconsistent")
    for field in (
        "swiotlb_segments",
        "raw_dma_phys_matches",
        "raw_dma_phys_mismatches",
        "phys_to_dma_matches",
        "phys_to_dma_mismatches",
        "dma_to_phys_matches",
        "dma_to_phys_mismatches",
        "above_4g_segments",
    ):
        if values[field] > values["segments"]:
            raise ValueError(field + " exceeds observed segments")

    complete = values["observation_complete"] == 1
    expected_raw = int(
        complete
        and values["raw_dma_phys_matches"] == values["segments"]
        and values["raw_dma_phys_mismatches"] == 0
    )
    expected_forward = int(
        complete
        and values["phys_to_dma_matches"] == values["segments"]
        and values["phys_to_dma_mismatches"] == 0
    )
    expected_inverse = int(
        complete
        and values["dma_to_phys_matches"] == values["segments"]
        and values["dma_to_phys_mismatches"] == 0
    )
    expected_no_swiotlb = int(complete and values["swiotlb_segments"] == 0)
    expected_direct = int(
        expected_raw
        and expected_forward
        and expected_inverse
        and expected_no_swiotlb
        and values["dma_range_identity"] == 1
    )
    summaries = {
        "all_prdt_entries_match": int(complete),
        "all_raw_dma_equals_original_phys": expected_raw,
        "all_phys_to_dma_matches": expected_forward,
        "all_dma_to_phys_matches": expected_inverse,
        "no_swiotlb_observed": expected_no_swiotlb,
        "observed_direct_identity_route": expected_direct,
    }
    for field, expected in summaries.items():
        if values[field] != expected:
            raise ValueError("inconsistent PRDT v3 summary flag: " + field)
    return values


def evaluate_observations(before, after):
    delta = {}
    for field in sorted(COUNTER_FIELDS):
        if after[field] < before[field]:
            raise ValueError("PRDT v3 counter moved backwards: " + field)
        delta[field] = after[field] - before[field]

    errors = []
    if delta["commands"] <= 0:
        errors.append("no new UFS command reached the v3 observer")
    if delta["segments"] <= 0:
        errors.append("no new UFS DMA segment reached the v3 observer")
    if delta["read_commands"] <= 0:
        errors.append("the bounded window contained no read command")
    for field in sorted(ZERO_REQUIRED_FIELDS):
        if after[field] != 0:
            errors.append(field + " is non-zero")
    for field in (
        "raw_dma_phys_matches",
        "phys_to_dma_matches",
        "dma_to_phys_matches",
    ):
        if after[field] != after["segments"]:
            errors.append(field + " does not cover every segment")
    required_flags = (
        "coherent_snapshot",
        "runtime_direct_dma_contract",
        "dma_range_identity",
        "dma_range_stable",
        "swiotlb_pool_present",
        "observation_complete",
        "all_prdt_entries_match",
        "all_raw_dma_equals_original_phys",
        "all_phys_to_dma_matches",
        "all_dma_to_phys_matches",
        "no_swiotlb_observed",
        "observed_direct_identity_route",
    )
    for field in required_flags:
        if after[field] != 1:
            errors.append(field + " is not proven")
    if after["swiotlb_force_bounce"] != 0:
        errors.append("the live UFS device forces SWIOTLB bouncing")
    if (
        after["dma_range_cpu_start"] != 0
        or after["dma_range_dma_start"] != 0
        or after["dma_range_offset"] != 0
        or after["dma_range_size"] != EXPECTED_DMA_RANGE_SIZE
    ):
        errors.append("the live DMA range differs from the pinned 36-bit identity window")
    if after["min_dma_address"] > after["max_dma_end"]:
        errors.append("invalid observed DMA extent")
    if after["min_original_phys"] > after["max_original_phys_end"]:
        errors.append("invalid observed physical extent")

    direct = not errors
    return {
        "passed": direct,
        "errors": errors,
        "delta": delta,
        "route_classification": (
            "raw-dma-equals-original-pa-no-swiotlb-under-live-identity-map"
            if direct
            else "direct-identity-route-not-proven"
        ),
        "live_dma_range_map_is_identity": bool(
            after["dma_range_identity"]
        ),
        "raw_dma_address_equals_original_phys_proven": bool(
            after["all_raw_dma_equals_original_phys"]
        ),
        "forward_and_inverse_translation_proven": bool(
            after["all_phys_to_dma_matches"]
            and after["all_dma_to_phys_matches"]
        ),
        "swiotlb_bounce_observed": bool(after["swiotlb_segments"]),
        "swiotlb_force_bounce": bool(after["swiotlb_force_bounce"]),
        "read_workload_causality_proven": False,
        "physical_firewall_bypass_proven": False,
        "xnu_cache_ownership_proven": False,
    }


BASE = load_base()
BASE.APPROVAL_PREFIX = APPROVAL_PREFIX
BASE.MODULE_NAME = MODULE_NAME
BASE.SYSFS_ATTRIBUTE = SYSFS_ATTRIBUTE
BASE.DECIMAL_FIELDS = DECIMAL_FIELDS
BASE.HEX_FIELDS = HEX_FIELDS
BASE.COUNTER_FIELDS = COUNTER_FIELDS
BASE.ZERO_REQUIRED_FIELDS = ZERO_REQUIRED_FIELDS
BASE.parse_observation = parse_observation
BASE.evaluate_observations = evaluate_observations
approval_token = BASE.approval_token


if __name__ == "__main__":
    raise SystemExit(BASE.main())
