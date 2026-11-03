#!/usr/bin/env python3
"""Test the fail-closed MT6897 UFS DMA-map candidate locally."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools/assess-mt6897-ufs-dma-map.py"
FDT = REPO.parent / "phone-fdt.bin"
RUNTIME = REPO / "research/mt6897-dma-ownership/live-20261101-v2/result.json"
PRDT = REPO / "research/mt6897-dma-ownership/prdt-interpretation-20261101-v1/interpretation.json"

SPEC = importlib.util.spec_from_file_location("mt6897_dma_map_candidate", TOOL)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load DMA-map candidate tool")
MODULE = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(MODULE)


class DmaMapModelTests(unittest.TestCase):
    def test_identity_window_boundaries(self):
        windows = [{"cpu_start": 0, "dma_start": 0, "bytes": 0x1000,
                    "offset": 0, "identity": True}]
        for address, size in ((0, 1), (0xfff, 1), (0x800, 0x800)):
            dma = MODULE.translate_pa_to_dma(windows, address, size)
            self.assertEqual(dma, address)
            self.assertEqual(MODULE.translate_dma_to_pa(windows, dma, size), address)

    def test_nonidentity_window_matches_linux_offset_rule(self):
        windows = [{"cpu_start": 0x80000000, "dma_start": 0x10000000,
                    "bytes": 0x2000, "offset": 0x70000000,
                    "identity": False}]
        self.assertEqual(
            MODULE.translate_pa_to_dma(windows, 0x80000120, 0x80),
            0x10000120,
        )
        self.assertEqual(
            MODULE.translate_dma_to_pa(windows, 0x10000120, 0x80),
            0x80000120,
        )

    def test_dma_above_cpu_window(self):
        windows = [{"cpu_start": 0x1000, "dma_start": 0x9000,
                    "bytes": 0x1000, "offset": -0x8000,
                    "identity": False}]
        self.assertEqual(MODULE.translate_pa_to_dma(windows, 0x1800, 1), 0x9800)
        self.assertEqual(MODULE.translate_dma_to_pa(windows, 0x9800, 1), 0x1800)

    def test_crossing_and_unmapped_requests_fail_closed(self):
        windows = [{"cpu_start": 0x1000, "dma_start": 0x2000,
                    "bytes": 0x100, "offset": -0x1000,
                    "identity": False}]
        for address, size in ((0xfff, 1), (0x10ff, 2), (0x1100, 1)):
            with self.assertRaisesRegex(ValueError, "unmapped or ambiguous"):
                MODULE.translate_pa_to_dma(windows, address, size)

    def test_ambiguous_overlapping_windows_fail_closed(self):
        windows = [
            {"cpu_start": 0, "dma_start": 0, "bytes": 0x1000,
             "offset": 0, "identity": True},
            {"cpu_start": 0x800, "dma_start": 0x1800, "bytes": 0x1000,
             "offset": -0x1000, "identity": False},
        ]
        with self.assertRaisesRegex(ValueError, "unmapped or ambiguous"):
            MODULE.translate_pa_to_dma(windows, 0x900, 1)

    def test_zero_length_and_uint64_overflow_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "non-zero"):
            MODULE.checked_end(0, 0, "test")
        with self.assertRaisesRegex(ValueError, "overflows"):
            MODULE.checked_end(MODULE.U64_MAX, 2, "test")

    def test_pinned_evidence_stays_candidate_only(self):
        self.assertTrue(FDT.is_file(), "missing saved phone-fdt.bin")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    str(output),
                    "--fdt", str(FDT),
                    "--runtime-evidence", str(RUNTIME),
                    "--prdt-evidence", str(PRDT),
                ],
                cwd=REPO,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertTrue(report["candidate"]["static_dt_translation_model_proven"])
            self.assertFalse(report["candidate"]["runtime_dma_range_entries_proven"])
            self.assertFalse(report["candidate"]["raw_dma_equals_cpu_pa_proven"])
            self.assertFalse(report["candidate"]["direct_route_receipt_issuable"])
            self.assertEqual(report["bounce"]["disposition"], "unknown")
            self.assertTrue(report["bounce"]["sample_no_swiotlb"])
            self.assertFalse(report["bounce"]["global_bounce_disposition_proven"])
            self.assertFalse(report["bounce"]["bounce_route_receipt_issuable"])
            self.assertFalse(report["safety"]["physical_backend_enabled"])
            self.assertEqual(report["bounce"]["sample_segments"], 17437)
            self.assertEqual(report["candidate"]["windows"], [{
                "bytes": "0x1000000000",
                "cpu_start": "0x0",
                "dma_start": "0x0",
                "identity": True,
                "offset": 0,
            }])
            second = subprocess.run(
                [
                    sys.executable, str(TOOL), str(output),
                    "--fdt", str(FDT),
                    "--runtime-evidence", str(RUNTIME),
                    "--prdt-evidence", str(PRDT),
                ],
                cwd=REPO,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("preserve existing output", second.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
