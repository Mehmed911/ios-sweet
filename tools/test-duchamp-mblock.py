#!/usr/bin/env python3
"""Bounded parser regression tests; synthetic records convey no ownership."""

import struct
import unittest

from duchamp_mblock import SIZE, RESERVED_OFFSET, RESERVED_STRIDE, decode_mblock


def fixture():
    raw = bytearray(SIZE)
    struct.pack_into("<Q", raw, 0, 2)
    struct.pack_into("<QQQ", raw, 8, 0x1000, 0x3000, 0)
    struct.pack_into("<QQQ", raw, 32, 0x8000, 0x2000, 1)
    struct.pack_into("<4I", raw, 0xc08, 0x99999999, 2, 1, 0)
    offset = RESERVED_OFFSET + 9 * RESERVED_STRIDE
    struct.pack_into("<QQI", raw, offset, 0x4000, 0x4000, 0)
    raw[offset + 20:offset + 25] = b"BL31\0"
    return raw


class MblockTests(unittest.TestCase):
    def test_holes_and_non_authorization(self):
        result = decode_mblock(fixture())
        self.assertEqual(result["reserved"][0]["slot"], 9)
        self.assertEqual(len(result["free"]), 2)
        self.assertFalse(result["physical_execution_authorized"])

    def test_stale_free_slots_are_not_allocations(self):
        raw = fixture()
        struct.pack_into("<QQQ", raw, 8 + 24 * 2, 0x1000, 0x1000, 0)
        self.assertEqual(len(decode_mblock(raw)["free"]), 2)

    def test_all_128_reservation_slots_are_inspected(self):
        raw = fixture()
        source = RESERVED_OFFSET + 9 * RESERVED_STRIDE
        target = RESERVED_OFFSET + 127 * RESERVED_STRIDE
        raw[target:target + RESERVED_STRIDE] = raw[source:source + RESERVED_STRIDE]
        raw[source:source + RESERVED_STRIDE] = bytes(RESERVED_STRIDE)
        self.assertEqual(decode_mblock(raw)["reserved"][0]["slot"], 127)

    def test_invalid_header(self):
        for offset, value in ((0xc08, 0), (0xc0c, 3), (0xc14, 1)):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                raw = fixture()
                struct.pack_into("<I", raw, offset, value)
                decode_mblock(raw)

    def test_size_is_exact(self):
        for raw in (b"", fixture()[:-1], fixture() + b"\0"):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                decode_mblock(raw)

    def test_count_limits(self):
        for offset, value, fmt in ((0, 0, "<Q"), (0, 129, "<Q"),
                                   (0xc10, 129, "<I"), (0xc10, 0, "<I")):
            with self.subTest(value=value, offset=offset), self.assertRaises(ValueError):
                raw = fixture()
                struct.pack_into(fmt, raw, offset, value)
                decode_mblock(raw)

    def test_unused_reserved_slot_with_data(self):
        raw = fixture()
        raw[RESERVED_OFFSET + 20] = 1
        with self.assertRaises(ValueError):
            decode_mblock(raw)

    def test_partial_interval(self):
        raw = fixture()
        struct.pack_into("<Q", raw, RESERVED_OFFSET + 9 * RESERVED_STRIDE + 8, 0)
        with self.assertRaises(ValueError):
            decode_mblock(raw)

    def test_integer_overflow(self):
        raw = fixture()
        struct.pack_into("<QQ", raw, 8, (1 << 64) - 0x1000, 0x2000)
        with self.assertRaises(ValueError):
            decode_mblock(raw)

    def test_unaligned_range(self):
        for offset in (8, RESERVED_OFFSET + 9 * RESERVED_STRIDE):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                raw = fixture()
                struct.pack_into("<Q", raw, offset, 0x4001)
                decode_mblock(raw)

    def test_unknown_rank_or_mapping(self):
        for offset, fmt in ((8 + 16, "<Q"), (RESERVED_OFFSET + 9 * RESERVED_STRIDE + 16, "<I")):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                raw = fixture()
                struct.pack_into(fmt, raw, offset, 2)
                decode_mblock(raw)

    def test_invalid_name(self):
        offset = RESERVED_OFFSET + 9 * RESERVED_STRIDE + 20
        for value in (bytes(128), b"A" * 128, b"\xff\0" + bytes(126), b"\n\0" + bytes(126)):
            with self.subTest(value=value[:2]), self.assertRaises(ValueError):
                raw = fixture()
                raw[offset:offset + 128] = value
                decode_mblock(raw)

    def test_free_reserved_overlap(self):
        raw = fixture()
        struct.pack_into("<Q", raw, 8, 0x2000)
        with self.assertRaises(ValueError):
            decode_mblock(raw)

    def test_free_free_overlap(self):
        raw = fixture()
        struct.pack_into("<Q", raw, 32, 0x3000)
        with self.assertRaises(ValueError):
            decode_mblock(raw)

    def test_reserved_reserved_overlap(self):
        raw = fixture()
        source = RESERVED_OFFSET + 9 * RESERVED_STRIDE
        raw[RESERVED_OFFSET:RESERVED_OFFSET + RESERVED_STRIDE] = raw[source:source + RESERVED_STRIDE]
        struct.pack_into("<I", raw, 0xc10, 2)
        with self.assertRaises(ValueError):
            decode_mblock(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
