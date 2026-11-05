#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/verify-duchamp-ufs-resource-bindings.py"
CAPTURE = (
    REPO / "duchamp/diagnostics/ufs-resource-bindings/"
    "PHONE-RESULT-2026-11-05.json"
)
SPEC = importlib.util.spec_from_file_location("verify_resource_bindings", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(MODULE)


class ResourceBindingVerificationTests(unittest.TestCase):
    def test_pinned_capture_passes_without_xnu_promotion(self):
        result = MODULE.verify_capture(CAPTURE.read_bytes())
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["verdict"],
            "linux-resource-bindings-observed-xnu-delegation-denied",
        )
        self.assertEqual(result["capture"]["provider_bindings"], 8)
        self.assertEqual(result["capture"]["regulators"], 3)
        self.assertEqual(result["capture"]["ufs_irq_handlers"], 9)
        for key in MODULE.FALSE_BOUNDARY:
            self.assertFalse(result["proofs"][key])
        self.assertFalse(result["authorization"]["physical_backend_enabled"])

    def test_hash_mismatch_is_rejected(self):
        raw = CAPTURE.read_bytes() + b"\n"
        with self.assertRaisesRegex(ValueError, "hash differs"):
            MODULE.verify_capture(raw)

    def test_xnu_delegation_promotion_is_rejected_after_hash_gate(self):
        report = json.loads(CAPTURE.read_text(encoding="utf-8"))
        report["proof_boundary"][
            "xnu_mmio_clock_reset_phy_regulator_irq_delegation_proven"
        ] = True
        raw = (json.dumps(report, sort_keys=True) + "\n").encode()
        with mock.patch.object(
            MODULE, "CAPTURE_SHA256", __import__("hashlib").sha256(raw).hexdigest()
        ):
            with self.assertRaisesRegex(ValueError, "overclaimed"):
                MODULE.verify_capture(raw)


if __name__ == "__main__":
    unittest.main()
