#!/usr/bin/env python3
"""Exercise the services RAM-root preflight against two archived payloads."""
import argparse
import hashlib
from pathlib import Path
import runpy
import struct
import unittest


def run(phone_payload, qemu_payload):
    packager = runpy.run_path(str(Path(__file__).with_name('package-duchamp-services-candidate.py')))
    inspect_payload = packager['inspect_payload']

    class PayloadPreflight(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.blob = bytearray(phone_payload.read_bytes())
            cls.adt_offset, cls.adt_size = struct.unpack_from('<2Q', cls.blob, 0x20)
            cls.segment = 0x2a8 + 10 * 32
            cls.ram_va, _, cls.ram_offset, _ = struct.unpack_from('<4Q', cls.blob, cls.segment)
            cls.prop = cls.blob.index(b'RAMDisk\0', cls.adt_offset, cls.adt_offset + cls.adt_size)

        def reject(self, offset, replacement, error):
            stop = offset + len(replacement)
            original = self.blob[offset:stop]
            try:
                self.blob[offset:stop] = replacement
                with self.assertRaisesRegex(ValueError, error):
                    inspect_payload(self.blob)
            finally:
                self.blob[offset:stop] = original

        def test_phone_payload(self):
            self.assert_ramdisk(self.blob)

        def test_qemu_payload(self):
            self.assert_ramdisk(qemu_payload.read_bytes())

        def assert_ramdisk(self, blob):
            plan = inspect_payload(blob)
            _, _, offset, size = struct.unpack_from('<4Q', blob, self.segment)
            self.assertEqual(plan['ramdisk_pa'], 0x1c2568000)
            self.assertEqual(plan['ramdisk_size'], size)
            self.assertEqual(hashlib.sha256(memoryview(blob)[offset:offset + size]).hexdigest(),
                             packager['PINS']['root.hfs'])

        def test_truncated_segment_table(self):
            with self.assertRaisesRegex(ValueError, 'truncated payload segment table'):
                inspect_payload(self.blob[:self.segment + 31])

        def test_storage_root_argument(self):
            offset = self.blob.index(b'rd=md0', 0x48, 0x2a8)
            self.reject(offset, b'rd=sd0', 'unexpected command line')

        def test_wrong_root_bytes_at_same_size(self):
            self.reject(self.ram_offset, bytes([self.blob[self.ram_offset] ^ 1]),
                        'embedded RAM root does not match guest proof')

        def test_segment_past_adt(self):
            self.reject(self.segment + 16, struct.pack('<Q', self.adt_offset + 1),
                        'invalid segment file range')

        def test_segment_outside_ram_window(self):
            self.reject(self.segment, struct.pack('<Q', self.ram_va + 0x20000000),
                        'RAM root outside payload window')

        def test_wrong_adt_address(self):
            self.reject(self.prop + 36, struct.pack('<Q', 0x1c2569000),
                        'ADT RAMDisk does not point')

        def test_missing_adt_property(self):
            self.reject(self.prop, b'RAMFail', 'ADT RAMDisk does not point')

        def test_truncated_adt(self):
            self.reject(0x28, struct.pack('<Q', self.adt_size - 8), 'invalid payload ADT')

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PayloadPreflight)
    return unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phone_payload', type=Path)
    parser.add_argument('qemu_payload', type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.phone_payload, args.qemu_payload) else 1)
