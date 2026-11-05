#!/usr/bin/env python3
"""Tests for the evidence-bound Duchamp UFS SiP ABI verifier."""

import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools/verify-duchamp-ufs-sip-abi.py"
PINNED = (
    REPO / "duchamp/diagnostics/ufs-sip-abi/"
           "VERIFICATION-2026-11-05.json"
)
SAVED_AUDIT = REPO / "research/mt6897-contract/audit-v3/result.json"
LIVE_RUNTIME = (
    REPO / "research/mt6897-live-evidence/14480520-210535/"
           "runtime-report-v7.json"
)
BL31_AUDIT = (
    REPO / "research/mt6897-firmware-live/20261101-v1/"
           "ufs-sip-audit-v2.json"
)
BL31_IDENTITY = (
    REPO / "duchamp/diagnostics/bl31-runtime-identity/"
           "VERIFICATION-2026-11-04.json"
)
SAVED_MODULE = (
    REPO / "research/mt6897-contract/audit-v3/ufs-mediatek-mod.ko"
)
RUNTIME_BUILD_ID_NOTE = (
    REPO / "research/mt6897-live-evidence/14480520-210535/"
           "ufs-module-build-id.note"
)
ATF = REPO / "research/mt6897-firmware-live/20261101-v1/atf.bin"

SPEC = importlib.util.spec_from_file_location("duchamp_ufs_sip_abi", TOOL)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load UFS SiP ABI verifier")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class UfsSipAbiTests(unittest.TestCase):
    def test_pinned_report_closes_only_static_abi(self):
        report = MODULE.validate_pinned_report(PINNED.read_bytes())
        proofs = report["proofs"]
        self.assertTrue(proofs["running_client_build_id_match_proven"])
        self.assertFalse(proofs["running_client_byte_equivalence_proven"])
        self.assertTrue(proofs["static_end_to_end_sip_abi_proven"])
        self.assertFalse(proofs["installed_binary_byte_equivalence_proven"])
        self.assertFalse(proofs["runtime_smc_effect_contract_proven"])
        self.assertFalse(proofs["firewall_state_proven"])
        self.assertFalse(proofs["xnu_firmware_abi_authorized"])
        self.assertFalse(proofs["physical_resource_ownership_proven"])

    def test_raw_evidence_reproduces_pinned_report(self):
        required = (
            SAVED_AUDIT, LIVE_RUNTIME, BL31_AUDIT, BL31_IDENTITY, SAVED_MODULE,
            RUNTIME_BUILD_ID_NOTE, ATF,
        )
        if not all(path.is_file() for path in required):
            self.skipTest("ignored local raw captures are not installed")
        report = MODULE.build_report(*(path.read_bytes() for path in required))
        pinned = MODULE.validate_pinned_report(PINNED.read_bytes())
        self.assertEqual(report, pinned)

    def test_tampered_pinned_report_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            MODULE.validate_pinned_report(PINNED.read_bytes() + b"\n")

    def test_client_and_firmware_selector_sets_are_exact(self):
        report = MODULE.validate_pinned_report(PINNED.read_bytes())
        self.assertEqual(report["client"]["abi"]["function_id"], "0xc2000276")
        self.assertEqual(
            report["client"]["abi"]["selectors"],
            {"refclk": 8, "mtcmos": 512, "mcq": 1024},
        )
        self.assertEqual(
            report["client"]["abi"]["selectors"],
            report["firmware"]["selectors"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
