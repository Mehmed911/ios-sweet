#!/usr/bin/env python3
"""Negative tests for the opt-in virtual input profile. No device operations."""
import argparse
import struct
import unittest
from pathlib import Path
import adt
import mkpayload
import qemu_ramroot_var as base
import qemu_pointer_profile as pointer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('baseline_payload', type=Path)
    a = ap.parse_args()
    original = a.baseline_payload.read_bytes()
    enabled = pointer.enable(original, True)

    def altered(change):
        data = bytearray(enabled)
        offset, size = struct.unpack_from('<2Q', data, 0x20)
        tree, _ = adt.parse(data[offset:offset + size])
        change(tree)
        dt = adt.serialize(tree)
        struct.pack_into('<Q', data, 0x28, len(dt))
        return data[:offset] + dt

    class Tests(unittest.TestCase):
        def reject(self, data):
            with self.assertRaises((ValueError, struct.error)):
                pointer.verify(data)

        def test_explicit_profile(self):
            self.assertEqual(pointer.verify(enabled), base.verify(original, diagnostic_hid=True))

        def test_default_denies_input(self):
            with self.assertRaises(ValueError):
                base.verify(enabled, diagnostic_hid=True)

        def test_wrong_virtual_address(self):
            def change(t):
                t.children[-1].props[-1] = ('reg', 0, struct.pack('<QQ', 0x112b0000, 0x200))
            self.reject(altered(change))

        def test_duplicate_node(self):
            self.reject(altered(lambda t: t.children.append(t.children[-1])))

        def test_missing_node(self):
            self.reject(altered(lambda t: t.children.pop()))

        def test_missing_argument(self):
            data = bytearray(enabled)
            text = base.BOOT_ARGS + ' sweethidtest=5'
            data[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = text.encode().ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
            self.reject(data)

        def test_wrong_compatible(self):
            self.reject(altered(lambda t: t.children[-1].props.__setitem__(1, ('compatible', 0, b'mt6897\0'))))

        def test_ufs_stays_denied(self):
            def change(t):
                n = adt.Node()
                n.props = [('name', 0, b'sweet-ufs\0')]
                t.children.append(n)
            self.reject(altered(change))

        def test_truncated_tree(self):
            self.reject(enabled[:-1])

        def test_double_enable_rejected(self):
            with self.assertRaises(ValueError):
                pointer.enable(enabled)

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
