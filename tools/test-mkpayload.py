#!/usr/bin/env python3
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import adt
import mkpayload


class RamdiskWindowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.kernel = Path(temp.name) / 'kernel'
        self.tree = Path(temp.name) / 'device.adt'
        self.disk = Path(temp.name) / 'root.img'
        self.kernel.write_bytes(b'kernel')
        self.phys_base = 0x1c0000000
        self.virt_base = 0xfffffe0006000000
        page = mkpayload.PAGE

        tree, chosen, memory_map = adt.Node(), adt.Node(), adt.Node()
        chosen.props = [('name', 0, b'chosen\0'),
                        ('dram-base', 0, struct.pack('<Q', self.phys_base)),
                        ('dram-size', 0, struct.pack('<Q', 4 * page))]
        memory_map.props = [('name', 0, b'memory-map\0')]
        chosen.children.append(memory_map)
        tree.children.append(chosen)
        self.tree.write_bytes(adt.serialize(tree))

        text = dict(name='__TEXT', vmaddr=self.virt_base, vmsize=page,
                    fileoff=0, filesize=self.kernel.stat().st_size)
        patcher = mock.patch.object(mkpayload, 'parse_macho', return_value=dict(
            segs=[text], entry=self.virt_base, fixups=None, cputype=0x100000c, cpusub=0))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_accepts_root_that_fits_with_adt_and_boot_args(self):
        self.disk.write_bytes(b'r' * mkpayload.PAGE)
        _, info = mkpayload.build(self.kernel, self.tree, 'rd=md0', self.disk)
        self.assertEqual(info['ramdisk'], (hex(self.phys_base + mkpayload.PAGE), hex(mkpayload.PAGE)))

    def test_rejects_oversize_before_reading_root(self):
        self.disk.write_bytes(b'r' * (mkpayload.PAGE + 1))
        with self.disk.open('rb') as source:
            disk = mock.MagicMock(wraps=source)
            disk.__enter__.return_value = disk
            with mock.patch.object(mkpayload, 'open', create=True,
                                   side_effect=lambda path, mode: disk if path == self.disk else open(path, mode)):
                with self.assertRaisesRegex(ValueError, 'RAM disk and boot data need 81920 bytes'):
                    mkpayload.build(self.kernel, self.tree, 'rd=md0', self.disk)
        disk.read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
