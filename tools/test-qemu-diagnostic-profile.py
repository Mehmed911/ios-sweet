#!/usr/bin/env python3
"""Check that virtual HID opt-in cannot broaden RAM-root or storage policy."""
import argparse
from pathlib import Path
import struct
import unittest
import qemu_ramroot_var as layout


def run(path):
    class Profile(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.payload = path.read_bytes()

        def test_explicit_virtual_hid(self):
            self.assertEqual(layout.verify(self.payload, diagnostic_hid=True)['var']['bytes'], 4 * 1024**2)

        def test_default_rejects_virtual_hid(self):
            with self.assertRaisesRegex(ValueError, 'boot arguments'):
                layout.verify(self.payload)

        def test_root_write_opt_in_rejected(self):
            with self.assertRaisesRegex(ValueError, 'boot arguments'):
                layout.verify(self.payload.replace(b'rootrw=0', b'rootrw=1', 1), diagnostic_hid=True)

        def test_arbitrary_hid_period_rejected(self):
            with self.assertRaisesRegex(ValueError, 'boot arguments'):
                layout.verify(self.payload.replace(b'sweethidtest=5', b'sweethidtest=1', 1), diagnostic_hid=True)

        def storage_node(self, name):
            data = bytearray(self.payload)
            offset, size = struct.unpack_from('<QQ', data, 0x20)
            tree, _ = layout.adt.parse(data[offset:offset+size])
            node = layout.adt.Node()
            node.props = [('name', 0, name.encode() + b'\0')]
            tree.children.append(node)
            encoded = layout.adt.serialize(tree)
            data[offset:] = encoded
            struct.pack_into('<Q', data, 0x28, len(encoded))
            with self.assertRaisesRegex(ValueError, 'storage-enabled ADT'):
                layout.verify(data, diagnostic_hid=True)

        def test_qemu_ufs_rejected(self):
            self.storage_node('duchamp-qemu-ufs')

        def test_legacy_ufs_rejected(self):
            self.storage_node('sweet-ufs')

        def test_truncated_image_rejected(self):
            with self.assertRaises(ValueError):
                layout.verify(self.payload[:-1], diagnostic_hid=True)

    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Profile)).wasSuccessful()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('payload', type=Path)
    raise SystemExit(0 if run(parser.parse_args().payload) else 1)
