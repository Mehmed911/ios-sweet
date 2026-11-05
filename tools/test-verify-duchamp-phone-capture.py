#!/usr/bin/env python3
"""Unit tests for the isolated Duchamp PC/x0 capture verifier."""

import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "verify-duchamp-phone-capture.py"
SPEC = importlib.util.spec_from_file_location(
    "verify_duchamp_phone_capture", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def encode_adr(register, pc, target):
    immediate = (target - pc) & ((1 << 21) - 1)
    return (0x10000000 | (immediate & 3) << 29 |
            (immediate >> 2) << 5 | register)


def encode_bl(pc, target):
    return 0x94000000 | (((target - pc) >> 2) & 0x3FFFFFF)


class PhoneCaptureVerifierTests(unittest.TestCase):
    def capture_fixture(self):
        raw = bytearray(256)
        capture = 64
        runtime_head = 208
        main = 128
        struct.pack_into("<IIII", raw, capture,
                         encode_adr(1, capture, 0),
                         encode_adr(2, capture + 4, runtime_head),
                         0xF9000041,
                         encode_bl(capture + 12, main))
        symbols = {
            "_head": 0,
            "duchamp_phone_capture_store_entry_pc": capture,
            "duchamp_bootshim_runtime_head": runtime_head,
            "duchamp_bootshim_main": main,
        }
        return raw, symbols

    def test_capture_sequence_resolves_pc_and_record(self):
        raw, symbols = self.capture_fixture()
        MODULE.verify_capture_store(bytes(raw), symbols)

    def test_capture_sequence_rejects_missing_store(self):
        raw, symbols = self.capture_fixture()
        struct.pack_into("<I", raw, 72, 0xD503201F)
        with self.assertRaisesRegex(ValueError, "str x1"):
            MODULE.verify_capture_store(bytes(raw), symbols)

    def test_arm64_image_requires_position_independent_header(self):
        raw = bytearray(64)
        struct.pack_into("<QQQ", raw, 8, 0, len(raw), 0xA)
        raw[56:60] = b"ARM\x64"
        self.assertEqual(MODULE.inspect_arm64_image(bytes(raw))["bytes"], 64)
        struct.pack_into("<Q", raw, 8, 0x80000)
        with self.assertRaisesRegex(ValueError, "offset zero"):
            MODULE.inspect_arm64_image(bytes(raw))

    def test_existing_output_is_preserved_before_reading_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaises(SystemExit) as raised:
                old_argv = __import__("sys").argv
                try:
                    __import__("sys").argv = [
                        str(SCRIPT), "--contract", "missing",
                        "--json-out", str(output)]
                    MODULE.main()
                finally:
                    __import__("sys").argv = old_argv
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
