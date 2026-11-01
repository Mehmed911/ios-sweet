#!/usr/bin/env python3
"""Tests for the full-XNU pre-GIC counter-probe verifier."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify-duchamp-counter-probe-xnu.py")
SPEC = importlib.util.spec_from_file_location("counter_xnu_verify", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CounterXnuVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"
        self.run.mkdir()
        self.kernel = self.root / "kernel"
        self.payload = self.root / "payload"
        self.adt = self.root / "adt"
        self.kernel.write_bytes(b"kernel")
        self.payload.write_bytes(b"payload")
        self.adt.write_bytes(b"adt")
        self.expected = {
            "kernel": MODULE.sha256(self.kernel),
            "payload": MODULE.sha256(self.payload),
            "adt": MODULE.sha256(self.adt),
        }
        self.result = {
            "status": "incomplete_decode",
            "unknown_glyphs": 3,
            "elapsed_host_seconds": 6.39,
            "stop_marker": MODULE.PASS_MARKER,
            "execution": {
                "clock": "default",
                "hardware_timing_claimed": False,
            },
        }
        self.screen = (
            "SWEET EARLY 20: kprintf startup complete\n"
            "SWEET EARLY 23: DUCHAMP COUNTER PROBE PASS\n???\n"
        )
        self.write_run()

    def write_run(self):
        (self.run / "result.json").write_text(
            json.dumps(self.result), encoding="utf-8")
        (self.run / "fb.txt").write_text(self.screen, encoding="utf-8")

    def verify(self):
        return MODULE.verify(
            self.run, self.kernel, self.payload, self.adt, self.expected)

    def test_explicit_pass_overrides_color_glyphs(self):
        report = self.verify()
        self.assertTrue(report["passed"])
        self.assertEqual(report["evidence"]["unknown_glyphs"], 3)
        self.assertFalse(report["scope"]["hardware_timer_proven"])
        self.assertFalse(report["scope"]["phone_access"])

    def test_panic_is_rejected(self):
        self.screen += "panic(cpu 0 caller 0x0): test\n"
        self.write_run()
        with self.assertRaisesRegex(ValueError, "failure marker"):
            self.verify()

    def test_fail_marker_is_rejected(self):
        self.screen = self.screen.replace("PASS", "FAIL")
        self.result["stop_marker"] = MODULE.PASS_MARKER
        self.write_run()
        with self.assertRaisesRegex(ValueError, "PASS marker"):
            self.verify()

    def test_missing_stop_marker_is_rejected(self):
        self.result["stop_marker"] = None
        self.write_run()
        with self.assertRaisesRegex(ValueError, "did not stop"):
            self.verify()

    def test_hash_mismatch_is_rejected_before_evidence(self):
        self.expected["kernel"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "kernel SHA-256"):
            self.verify()

    def test_hardware_claim_is_rejected(self):
        self.result["execution"]["hardware_timing_claimed"] = True
        self.write_run()
        with self.assertRaisesRegex(ValueError, "hardware-timing"):
            self.verify()


if __name__ == "__main__":
    unittest.main(verbosity=2)
