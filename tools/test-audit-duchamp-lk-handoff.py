#!/usr/bin/env python3
"""Unit tests for the offline Duchamp LK handoff audit."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "audit-duchamp-lk-handoff.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_duchamp_lk_handoff", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def mtk_fixture():
    raw = bytearray(b"\xff" * 0x240)
    payload = b"0123456789abcdef"
    struct.pack_into("<II", raw, 0, MODULE.MTK_OUTER_MAGIC, len(payload))
    raw[8:40] = b"\0" * 32
    raw[8:10] = b"lk"
    struct.pack_into("<II", raw, 0x30, MODULE.MTK_INNER_MAGIC,
                     MODULE.MTK_HEADER_BYTES)
    raw[MODULE.MTK_HEADER_BYTES:
        MODULE.MTK_HEADER_BYTES + len(payload)] = payload
    return raw, payload


def arm64_image_fixture(size=64):
    raw = bytearray(size)
    struct.pack_into("<QQQ", raw, 8, 0,
                     MODULE.STOCK_IMAGE_MEMORY_BYTES, 0xA)
    raw[56:60] = b"ARM\x64"
    return bytes(raw)


class HandoffAuditTests(unittest.TestCase):
    def test_mtk_package_parser_accepts_one_bounded_entry(self):
        raw, payload = mtk_fixture()
        entries = MODULE.parse_mtk_package(bytes(raw))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["name"], "lk")
        self.assertEqual(entries[0]["payload_offset"], 0x200)
        self.assertEqual(entries[0]["payload_sha256"],
                         MODULE.sha256(payload))

    def test_mtk_package_parser_rejects_header_mutations(self):
        raw, _ = mtk_fixture()
        raw[0] ^= 1
        with self.assertRaisesRegex(ValueError, "unexpected bytes"):
            MODULE.parse_mtk_package(bytes(raw))

        raw, _ = mtk_fixture()
        struct.pack_into("<I", raw, 0x30, 0)
        with self.assertRaisesRegex(ValueError, "inner magic"):
            MODULE.parse_mtk_package(bytes(raw))

    def test_arm64_image_contract_is_strict(self):
        result = MODULE.parse_arm64_image(arm64_image_fixture())
        self.assertEqual(result["text_offset"], 0)
        self.assertEqual(result["memory_bytes"],
                         MODULE.STOCK_IMAGE_MEMORY_BYTES)
        broken = bytearray(arm64_image_fixture())
        struct.pack_into("<Q", broken, 8, 0x80000)
        with self.assertRaisesRegex(ValueError, "text_offset"):
            MODULE.parse_arm64_image(bytes(broken))

    def test_boot_parser_keeps_static_and_runtime_claims_separate(self):
        image = arm64_image_fixture()
        compressed = b"fake-lz4"
        raw = bytearray(8192)
        raw[:8] = b"ANDROID!"
        struct.pack_into("<I", raw, 8, len(compressed))
        struct.pack_into("<I", raw, 20, 1584)
        struct.pack_into("<I", raw, 40, 4)
        raw[MODULE.BOOT_PAGE_BYTES:
            MODULE.BOOT_PAGE_BYTES + len(compressed)] = compressed
        with mock.patch.object(MODULE, "BOOT_SHA256",
                               MODULE.sha256(raw)), \
                mock.patch.object(MODULE, "BOOT_KERNEL_BYTES",
                                  len(compressed)), \
                mock.patch.object(MODULE, "STOCK_IMAGE_BYTES", len(image)), \
                mock.patch.object(MODULE, "STOCK_IMAGE_SHA256",
                                  MODULE.sha256(image)):
            result = MODULE.inspect_boot(
                bytes(raw), decompressor=lambda value: image)
        self.assertEqual(result["kernel_format"], "lz4-legacy")
        self.assertEqual(result["image"]["text_offset"], 0)

    def test_vendor_header_addresses_are_pinned(self):
        raw = bytearray(4096)
        raw[:8] = b"VNDRBOOT"
        struct.pack_into("<I", raw, 8, 4)
        struct.pack_into("<I", raw, 12, 4096)
        struct.pack_into("<I", raw, 16, MODULE.ANDROID_IMAGE_LOAD)
        struct.pack_into("<I", raw, 20, MODULE.VENDOR_RAMDISK_ADDRESS)
        struct.pack_into("<I", raw, 24, 0x1000)
        struct.pack_into("<I", raw, 2076, MODULE.LIVE_FDT_ADDRESS)
        struct.pack_into("<I", raw, 2096, 2128)
        struct.pack_into("<I", raw, 2100, 0x2000)
        struct.pack_into("<Q", raw, 2104, MODULE.LIVE_FDT_ADDRESS)
        with mock.patch.object(MODULE, "VENDOR_BOOT_SHA256",
                               MODULE.sha256(raw)):
            result = MODULE.inspect_vendor_boot(bytes(raw))
        self.assertEqual(result["kernel_addr"], MODULE.ANDROID_IMAGE_LOAD)
        self.assertEqual(result["dtb_addr"], MODULE.LIVE_FDT_ADDRESS)

        struct.pack_into("<Q", raw, 2104, MODULE.LIVE_FDT_ADDRESS + 0x1000)
        with mock.patch.object(MODULE, "VENDOR_BOOT_SHA256",
                               MODULE.sha256(raw)):
            with self.assertRaisesRegex(ValueError, "dtb_addr"):
                MODULE.inspect_vendor_boot(bytes(raw))

    def test_iomem_requires_exact_page_rounded_ranges(self):
        ranges = MODULE.parse_iomem(
            b"40000000-4807ffff : System RAM\n"
            b"  47c80000-47cf6fff : reserved\n")
        result = MODULE.find_iomem(
            ranges, MODULE.LIVE_FDT_ADDRESS,
            MODULE.LIVE_FDT_RESERVED_BYTES, "reserved")
        self.assertEqual(result["bytes"], MODULE.LIVE_FDT_RESERVED_BYTES)
        with self.assertRaisesRegex(ValueError, "lacks exact"):
            MODULE.find_iomem(
                ranges, MODULE.LIVE_FDT_ADDRESS,
                MODULE.LIVE_FDT_RESERVED_BYTES + 0x1000, "reserved")

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report.json"
            output.write_text("keep", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "--lk", "missing",
                 "--boot", "missing", "--vendor-boot", "missing",
                 "--fdt", "missing", "--iomem", "missing",
                 "--output", str(output)],
                capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertIn("preserve existing output", process.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
