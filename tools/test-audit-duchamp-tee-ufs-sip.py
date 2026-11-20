#!/usr/bin/env python3
"""Tests for the captured BL31 UFS SiP static audit."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/audit-duchamp-tee-ufs-sip.py"
SPEC = importlib.util.spec_from_file_location("audit_duchamp_tee_ufs_sip", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    raw = bytearray(0x66200)
    for _, (offset, encoded) in MODULE.PINNED_REGIONS.items():
        value = bytes.fromhex(encoded)
        raw[offset:offset + len(value)] = value
    name_offset = MODULE.UFS_NAME_ADDRESS - MODULE.ATF_LOAD_BASE
    name = MODULE.UFS_NAME.encode("ascii") + b"\0"
    raw[name_offset:name_offset + len(name)] = name
    index_offset = MODULE.UFS_RUNTIME_INDEX_ADDRESS - MODULE.ATF_LOAD_BASE
    struct.pack_into("<h", raw, index_offset, -1)
    return raw


class TeeUfsSipAuditTests(unittest.TestCase):
    def test_valid_static_paths_do_not_promote_runtime_effects(self):
        report = MODULE.audit_atf(bytes(fixture()))
        self.assertTrue(report["passed"])
        self.assertEqual(report["selectors"]["refclk"]["value"], 8)
        self.assertEqual(report["selectors"]["mtcmos"]["value"], 512)
        self.assertEqual(report["selectors"]["mcq"]["value"], 1024)
        self.assertTrue(
            report["claims"]["mtcmos_body_present_in_captured_binary"]
        )
        self.assertEqual(
            report["mtcmos_mmio"]["control_registers"],
            ["0x1c001e10", "0x1c001e14"],
        )
        self.assertTrue(
            report["claims"]["captured_bl31_mtcmos_mmio_paths_verified"]
        )
        self.assertFalse(
            report["claims"]["direct_xnu_mtcmos_mmio_authorized"]
        )
        self.assertFalse(
            report["claims"]["zero_reply_proves_physical_effect"]
        )
        self.assertFalse(
            report["claims"]["runtime_smc_return_effect_contract_verified"]
        )

    def test_changed_descriptor_is_rejected(self):
        raw = fixture()
        raw[0x66020] ^= 1
        with self.assertRaisesRegex(ValueError, "pinned BL31 region differs"):
            MODULE.audit_atf(bytes(raw))

    def test_changed_selector_branch_is_rejected(self):
        raw = fixture()
        raw[0x4508C] ^= 1
        with self.assertRaisesRegex(ValueError, "pinned BL31 region differs"):
            MODULE.audit_atf(bytes(raw))

    def test_changed_mtcmos_mmio_path_is_rejected(self):
        raw = fixture()
        raw[0x3A080] ^= 1
        with self.assertRaisesRegex(ValueError, "pinned BL31 region differs"):
            MODULE.audit_atf(bytes(raw))

    def test_changed_service_name_is_rejected(self):
        raw = fixture()
        offset = MODULE.UFS_NAME_ADDRESS - MODULE.ATF_LOAD_BASE
        raw[offset] ^= 1
        with self.assertRaisesRegex(ValueError, "service name differs"):
            MODULE.audit_atf(bytes(raw))

    def test_changed_registration_sentinel_is_rejected(self):
        raw = fixture()
        offset = MODULE.UFS_RUNTIME_INDEX_ADDRESS - MODULE.ATF_LOAD_BASE
        struct.pack_into("<h", raw, offset, 0)
        with self.assertRaisesRegex(ValueError, "registration sentinel"):
            MODULE.audit_atf(bytes(raw))

    def test_expected_receipt_is_enforced(self):
        raw = bytes(fixture())
        with self.assertRaisesRegex(ValueError, "size differs"):
            MODULE.audit_atf(raw, expected_bytes=len(raw) + 1)
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            MODULE.audit_atf(raw, expected_sha256="00" * 32)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            output.write_text("keep", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "missing", str(output)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
