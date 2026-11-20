#!/usr/bin/env python3
"""Tests for the local Duchamp tee_a inspector."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/inspect-duchamp-tee.py"
SPEC = importlib.util.spec_from_file_location("inspect_duchamp_tee", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    payload = bytearray(MODULE.EXPECTED_DECLARED_PAYLOAD_BYTES)
    cursor = 0x100
    for text in (
        MODULE.BL31_RELEASE,
        MODULE.BL31_BUILT,
        MODULE.BL31_SOFTWARE,
        MODULE.BL31_PLATFORM,
        MODULE.BL31_SOFTWARE_BUILT,
        MODULE.BL31_SOFTWARE_BUILD_HOST_TIME,
    ):
        encoded = text.encode("ascii")
        payload[cursor:cursor + len(encoded)] = encoded
        cursor += len(encoded) + 1

    payload_end = MODULE.EXPECTED_HEADER_BYTES + len(payload)
    next_offset = MODULE.align_up(payload_end, MODULE.ALIGNMENT)
    raw = bytearray(next_offset + MODULE.EXPECTED_HEADER_BYTES)
    struct.pack_into("<II", raw, 0, MODULE.OUTER_MAGIC, len(payload))
    raw[8:11] = b"atf"
    struct.pack_into("<II", raw, 0x30, MODULE.INNER_MAGIC,
                     MODULE.EXPECTED_HEADER_BYTES)
    raw[MODULE.EXPECTED_HEADER_BYTES:payload_end] = payload
    struct.pack_into("<I", raw, next_offset, MODULE.OUTER_MAGIC)
    raw[next_offset + 8:next_offset + 13] = b"cert1"
    struct.pack_into("<I", raw, next_offset + 0x30, MODULE.INNER_MAGIC)
    return raw


class TeeInspectorTests(unittest.TestCase):
    def test_valid_image_pins_binary_but_not_effects(self):
        report = MODULE.inspect_image(bytes(fixture()))
        self.assertTrue(report["passed"])
        self.assertEqual(report["atf_entry"]["next_entry_name"], "cert1")
        self.assertTrue(
            report["claims"]["bl31_runtime_identity_string_match_verified"]
        )
        self.assertFalse(
            report["claims"]["bl31_public_source_equivalence_verified"]
        )
        self.assertFalse(
            report["claims"]["bl31_ufs_sip_effect_contract_verified"]
        )

    def test_wrong_outer_magic_is_rejected(self):
        raw = fixture()
        raw[0] ^= 1
        with self.assertRaisesRegex(ValueError, "outer magic"):
            MODULE.inspect_image(bytes(raw))

    def test_wrong_declared_size_is_rejected(self):
        raw = fixture()
        struct.pack_into("<I", raw, 4,
                         MODULE.EXPECTED_DECLARED_PAYLOAD_BYTES - 1)
        with self.assertRaisesRegex(ValueError, "declared payload size"):
            MODULE.inspect_image(bytes(raw))

    def test_wrong_payload_offset_is_rejected(self):
        raw = fixture()
        struct.pack_into("<I", raw, 0x34, 0x100)
        with self.assertRaisesRegex(ValueError, "payload offset"):
            MODULE.inspect_image(bytes(raw))

    def test_nonzero_alignment_padding_is_rejected(self):
        raw = fixture()
        end = MODULE.EXPECTED_HEADER_BYTES + MODULE.EXPECTED_DECLARED_PAYLOAD_BYTES
        raw[end] = 1
        with self.assertRaisesRegex(ValueError, "alignment padding"):
            MODULE.inspect_image(bytes(raw))

    def test_wrong_next_entry_is_rejected(self):
        raw = fixture()
        end = MODULE.EXPECTED_HEADER_BYTES + MODULE.EXPECTED_DECLARED_PAYLOAD_BYTES
        next_offset = MODULE.align_up(end, MODULE.ALIGNMENT)
        raw[next_offset + 8:next_offset + 13] = b"other"
        with self.assertRaisesRegex(ValueError, "entry after atf"):
            MODULE.inspect_image(bytes(raw))

    def test_missing_or_duplicate_identity_is_rejected(self):
        raw = fixture()
        offset = raw.find(MODULE.BL31_RELEASE.encode("ascii"))
        raw[offset] = ord("x")
        with self.assertRaisesRegex(ValueError, "missing BL31 identity"):
            MODULE.inspect_image(bytes(raw))

        raw = fixture()
        encoded = MODULE.BL31_RELEASE.encode("ascii")
        duplicate = MODULE.EXPECTED_HEADER_BYTES + 0x1000
        raw[duplicate:duplicate + len(encoded)] = encoded
        with self.assertRaisesRegex(ValueError, "duplicate BL31 identity"):
            MODULE.inspect_image(bytes(raw))

    def test_expected_receipt_is_enforced(self):
        raw = bytes(fixture())
        with self.assertRaisesRegex(ValueError, "size differs"):
            MODULE.inspect_image(raw, expected_bytes=len(raw) + 1)
        with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
            MODULE.inspect_image(raw, expected_sha256="00" * 32)

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
