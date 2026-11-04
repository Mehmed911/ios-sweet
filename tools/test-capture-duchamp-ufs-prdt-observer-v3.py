#!/usr/bin/env python3
"""Tests for the fail-closed Duchamp PRDT v3 live runner."""

import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/capture-duchamp-ufs-prdt-observer-v3.py"
SPEC = importlib.util.spec_from_file_location("capture_prdt_v3", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def observation(**changes):
    values = {field: 0 for field in MODULE.DECIMAL_FIELDS | MODULE.HEX_FIELDS}
    values.update(
        {
            "observation_version": 3,
            "root_read_only": 1,
            "coherent_snapshot": 1,
            "runtime_direct_dma_contract": 1,
            "dma_range_count": 1,
            "dma_range_terminated": 1,
            "dma_range_identity": 1,
            "dma_range_stable": 1,
            "dma_range_size": MODULE.EXPECTED_DMA_RANGE_SIZE,
            "swiotlb_pool_present": 1,
            "swiotlb_pool_active": 1,
            "runtime_bus_dma_limit": MODULE.BASE.EXPECTED_BUS_DMA_LIMIT,
        }
    )
    values.update(changes)
    return values


def render(values):
    lines = []
    for key in sorted(values):
        value = values[key]
        if key in MODULE.HEX_FIELDS:
            value = f"0x{value:016x}"
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def successful_after(**changes):
    values = observation(
        hook_calls=4,
        target_calls=4,
        commands=4,
        segments=8,
        read_commands=4,
        raw_dma_phys_matches=8,
        phys_to_dma_matches=8,
        dma_to_phys_matches=8,
        above_4g_segments=3,
        min_dma_address=0x1000,
        max_dma_end=0x100001FFF,
        min_original_phys=0x1000,
        max_original_phys_end=0x100001FFF,
        max_segment_length=0x1000,
        observation_complete=1,
        all_prdt_entries_match=1,
        all_raw_dma_equals_original_phys=1,
        all_phys_to_dma_matches=1,
        all_dma_to_phys_matches=1,
        no_swiotlb_observed=1,
        observed_direct_identity_route=1,
    )
    values.update(changes)
    return values


class CapturePrdtV3Tests(unittest.TestCase):
    def test_parser_field_set_matches_kernel_report(self):
        source = (
            ROOT
            / "duchamp/diagnostics/ufs-prdt-observer-v3/duchamp_ufs_prdt_observer_v3.c"
        ).read_text(encoding="utf-8")
        report_fields = set(re.findall(r'"([a-z0-9_]+)=', source))
        self.assertEqual(report_fields, MODULE.DECIMAL_FIELDS | MODULE.HEX_FIELDS)

    def test_wrapper_pins_v3_module_and_attribute(self):
        self.assertEqual(MODULE.BASE.MODULE_NAME, MODULE.MODULE_NAME)
        self.assertEqual(MODULE.BASE.SYSFS_ATTRIBUTE, MODULE.SYSFS_ATTRIBUTE)
        self.assertTrue(MODULE.MODULE_NAME.endswith("_v3"))
        self.assertTrue(MODULE.SYSFS_ATTRIBUTE.endswith("_v3"))

    def test_direct_identity_observation_passes(self):
        before = MODULE.parse_observation(render(observation()))
        after = MODULE.parse_observation(render(successful_after()))
        result = MODULE.evaluate_observations(before, after)
        self.assertTrue(result["passed"])
        self.assertTrue(result["live_dma_range_map_is_identity"])
        self.assertTrue(result["raw_dma_address_equals_original_phys_proven"])
        self.assertFalse(result["swiotlb_bounce_observed"])

    def test_shifted_range_fails_closed(self):
        before = MODULE.parse_observation(render(observation()))
        shifted = successful_after(
            dma_range_cpu_start=0x100000000,
            dma_range_dma_start=0x20000000,
            dma_range_offset=0xE0000000,
            dma_range_identity=0,
            all_raw_dma_equals_original_phys=0,
            observed_direct_identity_route=0,
            raw_dma_phys_matches=0,
            raw_dma_phys_mismatches=8,
        )
        after = MODULE.parse_observation(render(shifted))
        result = MODULE.evaluate_observations(before, after)
        self.assertFalse(result["passed"])

    def test_swiotlb_segment_fails_closed(self):
        before = MODULE.parse_observation(render(observation()))
        bounced = successful_after(
            swiotlb_segments=8,
            raw_dma_phys_matches=0,
            raw_dma_phys_mismatches=8,
            phys_to_dma_matches=0,
            phys_to_dma_mismatches=8,
            all_raw_dma_equals_original_phys=0,
            all_phys_to_dma_matches=0,
            no_swiotlb_observed=0,
            observed_direct_identity_route=0,
        )
        after = MODULE.parse_observation(render(bounced))
        result = MODULE.evaluate_observations(before, after)
        self.assertFalse(result["passed"])
        self.assertTrue(result["swiotlb_bounce_observed"])

    def test_parser_rejects_unknown_duplicate_and_bad_offset(self):
        text = render(observation())
        with self.assertRaisesRegex(ValueError, "unexpected"):
            MODULE.parse_observation(text + "\nfuture=1")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MODULE.parse_observation(text + "\nsegments=0")
        bad = observation(dma_range_offset=1)
        with self.assertRaisesRegex(ValueError, "offset"):
            MODULE.parse_observation(render(bad))

    def test_approval_token_is_bound_to_exact_hash(self):
        token = MODULE.approval_token("a" * 64)
        self.assertEqual(
            token,
            MODULE.APPROVAL_PREFIX + "A" * 64,
        )

    def test_physical_ownership_is_not_claimed(self):
        before = MODULE.parse_observation(render(observation()))
        after = MODULE.parse_observation(render(successful_after()))
        result = MODULE.evaluate_observations(before, after)
        self.assertFalse(result["physical_firewall_bypass_proven"])
        self.assertFalse(result["xnu_cache_ownership_proven"])
        self.assertFalse(result["read_workload_causality_proven"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
