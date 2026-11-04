#!/usr/bin/env python3
"""Tests for the pinned Duchamp PRDT v3 result interpreter."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/interpret-duchamp-prdt-v3-observation.py"
RESULT = (
    ROOT
    / "duchamp/diagnostics/ufs-prdt-observer-v3/PHONE-RESULT-2026-11-04.json"
)
SPEC = importlib.util.spec_from_file_location("interpret_prdt_v3", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InterpretPrdtV3Tests(unittest.TestCase):
    def test_pinned_result_validates_without_overclaiming(self):
        report = MODULE.validate(RESULT)
        self.assertEqual(report["verdict"], "validated-live-direct-dma-evidence")
        proven = report["proven"]
        self.assertTrue(proven["live_dma_range_is_identity"])
        self.assertTrue(proven["raw_dma_equals_cpu_pa_for_all_observed_segments"])
        self.assertTrue(proven["swiotlb_pool_inactive"])
        self.assertEqual(proven["observed_segments_total"], 34162)
        self.assertEqual(proven["observed_segments_in_bounded_window"], 29452)
        self.assertFalse(
            report["not_proven"]["physical_firewall_or_secure_firmware_delegation"]
        )
        self.assertFalse(report["not_proven"]["xnu_cache_maintenance_ownership"])

    def test_tampered_result_is_rejected_by_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            path.write_bytes(RESULT.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                MODULE.validate(path)

    def test_output_is_create_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt.json"
            report = MODULE.validate(RESULT)
            self.assertTrue(report["proven"]["cleanup_complete"])
            output.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "preserve existing output"):
                MODULE.require(not output.exists(), "preserve existing output")


if __name__ == "__main__":
    unittest.main(verbosity=2)
