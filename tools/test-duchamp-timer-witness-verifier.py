#!/usr/bin/env python3
"""Unit tests for raw and qemu-sweet PNG timer-IRQ witness verification."""

import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify-duchamp-timer-irq-witness.py")
SPEC = importlib.util.spec_from_file_location("duchamp_timer_witness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


WIDTH = 5
HEIGHT = 4
STRIDE = 24
MARKER_WIDTH = 2
MARKER_HEIGHT = 2
PIXEL = MODULE.DEFAULT_PIXEL


def make_raw(*, boundary=False):
    raw = bytearray(STRIDE * HEIGHT)
    for y in range(HEIGHT - MARKER_HEIGHT, HEIGHT):
        if boundary:
            struct.pack_into("<I", raw, y * STRIDE +
                             (WIDTH - MARKER_WIDTH - 1) * 4, PIXEL)
        for x in range(WIDTH - MARKER_WIDTH, WIDTH):
            struct.pack_into("<I", raw, y * STRIDE + x * 4, PIXEL)
    return bytes(raw)


def png_chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def make_png(raw, *, row_filter=0):
    rows = []
    for y in range(HEIGHT):
        rgb = bytearray()
        for x in range(WIDTH):
            pixel, = struct.unpack_from("<I", raw, y * STRIDE + x * 4)
            rgb.extend(((pixel >> 16) & 0xFF, (pixel >> 8) & 0xFF,
                        pixel & 0xFF))
        rows.append(bytes((row_filter,)) + bytes(rgb))
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    return (MODULE.PNG_SIGNATURE + png_chunk(b"IHDR", header) +
            png_chunk(b"IDAT", zlib.compress(b"".join(rows))) +
            png_chunk(b"IEND", b""))


class WitnessVerifierTests(unittest.TestCase):
    def verify(self, raw):
        return MODULE.verify_witness(
            raw, width=WIDTH, height=HEIGHT, stride=STRIDE,
            marker_width=MARKER_WIDTH, marker_height=MARKER_HEIGHT,
            expected=PIXEL)

    def test_raw_marker_passes(self):
        self.assertTrue(self.verify(make_raw())["passed"])

    def test_full_width_band_is_not_a_witness(self):
        result = self.verify(make_raw(boundary=True))
        self.assertFalse(result["passed"])
        self.assertEqual(result["boundary_rows_not_marker_color"], 0)

    def test_qemu_png_round_trip_passes(self):
        decoded = MODULE.decode_qemu_png(
            make_png(make_raw()), width=WIDTH, height=HEIGHT, stride=STRIDE)
        self.assertTrue(self.verify(decoded)["passed"])

    def test_png_crc_failure_is_rejected(self):
        png = bytearray(make_png(make_raw()))
        png[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            MODULE.decode_qemu_png(
                bytes(png), width=WIDTH, height=HEIGHT, stride=STRIDE)

    def test_nonzero_png_filter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "row filter"):
            MODULE.decode_qemu_png(
                make_png(make_raw(), row_filter=1),
                width=WIDTH, height=HEIGHT, stride=STRIDE)

    def test_loader_reports_source_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fb.png"
            path.write_bytes(make_png(make_raw()))
            raw, source_format = MODULE.load_framebuffer(
                path, width=WIDTH, height=HEIGHT, stride=STRIDE)
        self.assertEqual(source_format, "qemu-png")
        self.assertTrue(self.verify(raw)["passed"])


if __name__ == "__main__":
    unittest.main()
