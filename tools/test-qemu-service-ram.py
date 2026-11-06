#!/usr/bin/env python3
"""Safety boundaries for the separate QEMU large RAM loader."""
import hashlib
from pathlib import Path
import runpy
import struct
import unittest
import adt

MOD = runpy.run_path(str(Path(__file__).with_name('qemu-service-ram.py')))


class LayoutTests(unittest.TestCase):
    def fixture(self):
        raw = (MOD['REPO'] / 'research/mt6897-boot/bsd-service-split-ci41543710742-qemu-authorized.adt').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), MOD['ADT_PIN'])
        raw = MOD['virtual_tree'](raw)
        vb = 0xfffffe0000000000
        payload = bytearray(0x400 + len(raw))
        struct.pack_into('<8sII', payload, 0, b'SWEETXNU', 1, 1)
        struct.pack_into('<7Q', payload, 0x10, vb, vb, 0x400, len(raw), vb + 0x4000,
            MOD['PHYS_BASE'], MOD['WINDOW'])
        struct.pack_into('<4Q', payload, 0x2a8, vb, 0x4000, 0x300, 16)
        payload[0x400:] = raw
        return payload

    def test_large_root_is_separate_from_kernel_and_ram_bounds(self):
        result = MOD['layout'](self.fixture(), 3 << 30)
        self.assertGreaterEqual(result['root_pa'], MOD['PHYS_BASE'] + 0x4000)
        self.assertLessEqual(result['top'], MOD['PHYS_BASE'] + MOD['WINDOW'] - (256 << 20))
        tree, _ = adt.parse(result['adt'])
        memory = MOD['child'](MOD['child'](tree, 'chosen'), 'memory-map')
        self.assertEqual(struct.unpack('<2Q', memory.prop('RAMDisk')), (result['root_pa'], 3 << 30))

    def test_reject_phone_adt(self):
        with self.assertRaises(ValueError): MOD['virtual_tree'](b'phone')

    def test_reject_original_small_window(self):
        data = self.fixture(); struct.pack_into('<Q', data, 0x40, 0x20000000)
        with self.assertRaises(ValueError): MOD['layout'](data, 3 << 30)

    def test_reject_root_over_kernel(self):
        data = self.fixture(); vb = struct.unpack_from('<Q', data, 0x10)[0]
        struct.pack_into('<Q', data, 0x30, vb)
        with self.assertRaises(ValueError): MOD['layout'](data, 0x4000)

    def test_reject_segment_outside_payload(self):
        data = self.fixture(); struct.pack_into('<Q', data, 0x2a8 + 16, len(data) + 1)
        with self.assertRaises(ValueError): MOD['layout'](data, 0x4000)

    def test_reject_oversize_and_unaligned_root(self):
        for size in (0, 1, (3 << 30) + 0x4000):
            with self.assertRaises(ValueError): MOD['layout'](self.fixture(), size)


if __name__ == '__main__': unittest.main()
