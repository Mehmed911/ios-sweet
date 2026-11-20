#!/usr/bin/env python3
"""Reject ambiguous multitouch profiles while keeping base storage gates."""
import argparse
import struct
import unittest
from pathlib import Path
import adt
import mkpayload
import qemu_touch_profile as touch
import qemu_pointer_profile as pointer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pointer_payload', type=Path)
    a = ap.parse_args()
    original = a.pointer_payload.read_bytes()
    enabled = touch.enable(original)

    def mutate(f):
        offset, size = struct.unpack_from('<2Q', enabled, 0x20)
        tree, _ = adt.parse(enabled[offset:offset + size])
        f(tree)
        dt = adt.serialize(tree)
        result = bytearray(enabled[:offset])
        struct.pack_into('<Q', result, 0x28, len(dt))
        return result + dt

    class Tests(unittest.TestCase):
        def reject(self, data):
            with self.assertRaises((ValueError, struct.error)):
                touch.verify(data)

        def test_roundtrip(self):
            self.assertEqual(touch.verify(enabled), pointer.verify(original))

        def test_pointer_profile_denies_touch(self):
            with self.assertRaises(ValueError):
                pointer.verify(enabled)

        def test_missing_touch(self):
            self.reject(original)

        def test_missing_touch_flag(self):
            data = bytearray(enabled)
            command = data[mkpayload.CMDLINE:mkpayload.SEG_TABLE].split(b'\0')[0].replace(touch.ARG.encode(), b'')
            data[mkpayload.CMDLINE:mkpayload.SEG_TABLE] = command.ljust(mkpayload.BOOT_LINE_LENGTH, b'\0')
            self.reject(data)

        def test_wrong_address(self):
            def f(tree):
                node = next(n for n in tree.children if n.name == 'duchamp-qemu-multitouch')
                node.props[-1] = ('reg', 0, struct.pack('<QQ', 0x112b0000, 0x200))
            self.reject(mutate(f))

        def test_wrong_compatible(self):
            def f(tree):
                node = next(n for n in tree.children if n.name == 'duchamp-qemu-multitouch')
                node.props[1] = ('compatible', 0, b'mediatek,mt6897\0')
            self.reject(mutate(f))

        def test_duplicate_node(self):
            self.reject(mutate(lambda t: t.children.append(next(n for n in t.children if n.name == 'duchamp-qemu-multitouch'))))

        def test_ufs_remains_denied(self):
            def f(tree):
                node = adt.Node()
                node.props = [('name', 0, b'duchamp-qemu-ufs\0')]
                tree.children.append(node)
            self.reject(mutate(f))

        def test_wrong_pointer_transport_denied(self):
            def f(tree):
                node = next(n for n in tree.children if n.name == 'duchamp-qemu-pointer')
                node.props[-1] = ('reg', 0, struct.pack('<QQ', 0x0a003c00, 0x200))
            self.reject(mutate(f))

        def test_truncated(self):
            self.reject(enabled[:-1])
            self.reject(b'')

        def test_twice_enabled(self):
            with self.assertRaises(ValueError):
                touch.enable(enabled)
    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful()


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
