#!/usr/bin/env python3
"""Tests for the evidence-bound Duchamp BL31 identity verifier."""

import importlib.util
from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools/verify-duchamp-bl31-runtime-identity.py"
PINNED = (
    REPO / "duchamp/diagnostics/bl31-runtime-identity/"
           "VERIFICATION-2026-11-04.json"
)
TEE = REPO / "research/mt6897-firmware-live/20261101-v1/tee_a.bin"
RUNTIME_LOG = (
    REPO / "research/mt6897-shell-runtime/"
           "read-only-20261101-maxspeed-v1/root-atf_log_head.stdout.txt"
)
RUNTIME_REPORT = (
    REPO / "research/mt6897-shell-runtime/"
           "read-only-20261101-maxspeed-v1/result.json"
)

SPEC = importlib.util.spec_from_file_location("duchamp_bl31_identity", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Bl31RuntimeIdentityTests(unittest.TestCase):
    def test_pinned_identity_closes_only_identity_gate(self):
        report = MODULE.validate_pinned_report(PINNED.read_bytes())
        self.assertEqual(
            report["verdict"], "installed-bl31-runtime-identity-matched"
        )
        proofs = report["proofs"]
        self.assertTrue(proofs["installed_firmware_identity_proven"])
        self.assertFalse(proofs["installed_binary_byte_equivalence_proven"])
        self.assertFalse(proofs["runtime_smc_effect_contract_proven"])
        self.assertFalse(proofs["physical_resource_ownership_proven"])

    def test_local_raw_capture_reproduces_pinned_report(self):
        required = (TEE, RUNTIME_LOG, RUNTIME_REPORT)
        if not all(path.is_file() for path in required):
            self.skipTest("ignored local raw captures are not installed")
        generated = MODULE.build_report(
            TEE.read_bytes(), RUNTIME_LOG.read_bytes(),
            RUNTIME_REPORT.read_bytes()
        )
        pinned = MODULE.validate_pinned_report(PINNED.read_bytes())
        self.assertEqual(generated, pinned)

    def test_tampered_pinned_report_is_rejected(self):
        raw = PINNED.read_bytes()
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            MODULE.validate_pinned_report(raw + b"\n")

    def test_truncated_runtime_log_is_rejected_before_parsing(self):
        raw = (
            REPO / "duchamp/diagnostics/bl31-runtime-identity/"
                   "ATF-LOG-2026-11-01.txt"
        ).read_bytes()
        with self.assertRaisesRegex(ValueError, "size differs"):
            MODULE.extract_runtime_identity(raw[:-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
