#!/usr/bin/env python3
"""Tests for the pinned XNU cache-backend QEMU interpreter."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools/interpret-duchamp-xnu-cache-qemu.py"
RESULT = (
    REPO
    / "duchamp/diagnostics/ufs-cache-xnu-qemu/RAW-VERIFICATION-2026-11-04.json"
)
SPEC = importlib.util.spec_from_file_location("interpret_xnu_cache_qemu", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InterpretXnuCacheQemuTests(unittest.TestCase):
    def test_pinned_execution_validates_without_physical_overclaim(self):
        report = MODULE.validate(REPO, RESULT)
        self.assertEqual(
            report["verdict"], "validated-xnu-cache-primitives-in-qemu"
        )
        proven = report["proven"]
        self.assertTrue(proven["actual_xnu_kernel_executed"])
        self.assertTrue(proven["clean_to_poc_callback_executed"])
        self.assertTrue(proven["flush_to_poc_callback_executed"])
        self.assertEqual(proven["expected_barrier_calls"], 3)
        self.assertFalse(
            report["not_proven"]["mt6897_outer_or_system_cache_reachability"]
        )
        self.assertFalse(report["safety"]["physical_ufs_backend_enabled"])

    def test_tampered_result_is_rejected_by_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            path.write_bytes(RESULT.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "hash differs"):
                MODULE.validate(REPO, path)

    def test_ci_source_blob_mismatch_is_rejected(self):
        expected = dict(MODULE.SOURCE_BLOBS)
        path = next(iter(expected))
        expected[path] = "0" * 64
        with self.assertRaisesRegex(ValueError, "source hash differs"):
            MODULE.verify_commit_sources(REPO, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
