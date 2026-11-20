#!/usr/bin/env python3
"""Reject ambiguous or unsafe packaging of the two QEMU RAM volumes."""
import argparse
from pathlib import Path
import struct
import unittest

import qemu_ramroot_var as layout


def run(path):
    class DualImage(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.payload = bytearray(path.read_bytes())
            cls.adt_start, cls.adt_bytes = struct.unpack_from('<QQ', cls.payload, 0x20)
            count, = struct.unpack_from('<I', cls.payload, 12)
            cls.var_seg = layout.mkpayload.SEG_TABLE + (count - 1) * layout.SEGMENT.size
            cls.ro_seg = cls.var_seg - layout.SEGMENT.size

        def mutate(self, offset, replacement, expected):
            end = offset + len(replacement)
            old = self.payload[offset:end]
            try:
                self.payload[offset:end] = replacement
                with self.assertRaisesRegex(ValueError, expected):
                    layout.verify(self.payload)
            finally:
                self.payload[offset:end] = old

        def test_layout(self):
            verified = layout.verify(self.payload)
            self.assertEqual(verified['root']['pa'] + verified['root']['bytes'], verified['var']['pa'])
            self.assertNotEqual(verified['root']['sha256'], verified['var']['sha256'])

        def test_root_writable_argument(self):
            offset = self.payload.index(b'rootrw=0', 0x48, 0x2a8)
            self.mutate(offset, b'rootrw=1', 'incorrect QEMU boot arguments')

        def test_overlapping_file_ranges(self):
            file, = struct.unpack_from('<Q', self.payload, self.ro_seg + 16)
            self.mutate(self.var_seg + 16, struct.pack('<Q', file), 'invalid reservation boundaries')

        def test_root_and_var_both_point_to_same_address(self):
            va, = struct.unpack_from('<Q', self.payload, self.ro_seg)
            self.mutate(self.var_seg, struct.pack('<Q', va), 'invalid reservation boundaries')

        def test_truncated_adt(self):
            self.mutate(0x28, struct.pack('<Q', len(self.payload)), 'invalid ADT bytes')

        def test_disagreeing_var_property(self):
            prop = self.payload.index(layout.PROP.encode() + b'\0', self.adt_start)
            self.mutate(prop + 36, bytes(8), f'invalid {layout.PROP}')

        def test_missing_var_property(self):
            prop = self.payload.index(layout.PROP.encode() + b'\0', self.adt_start)
            self.mutate(prop, b'X', f'invalid {layout.PROP}')

        def test_overflowing_ram_window(self):
            self.mutate(0x40, b'\xff' * 8, 'invalid boot-data RAM window')

        def test_unaligned_var_size(self):
            self.mutate(self.var_seg + 8, struct.pack('<Q', layout.IMAGE_SIZE - 1), 'invalid var segment')

        def test_insufficient_ram_window(self):
            self.mutate(0x40, struct.pack('<Q', layout.PAGE), 'invalid boot-data RAM window')

        def test_kernel_overlaps_root(self):
            self.mutate(layout.mkpayload.SEG_TABLE + 8, struct.pack('<Q', 512 * 1024**2),
                        'kernel segment overlaps volumes')

        def test_malformed_hfs_header(self):
            file, = struct.unpack_from('<Q', self.payload, self.var_seg + 16)
            self.mutate(file + 1024, b'NO', 'invalid var segment')

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DualImage))
    return result.wasSuccessful()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('payload', type=Path)
    args = ap.parse_args()
    raise SystemExit(0 if run(args.payload) else 1)
