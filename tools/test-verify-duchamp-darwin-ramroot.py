#!/usr/bin/env python3
"""Native regression tests for the RAM-root evidence verifier."""
import argparse
from pathlib import Path
import runpy
import struct
import unittest


def run(output):
    verifier = runpy.run_path(str(Path(__file__).with_name('verify-duchamp-darwin-ramroot.py')))
    check_ramdisk = verifier['check_ramdisk']
    check_execution = verifier['check_execution']

    class RamRootEvidence(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.payload = bytearray((output / 'payload.bin').read_bytes())
            cls.root = (output / 'root.hfs').read_bytes()
            cls.result = {'status': 'no_panic_observed', 'unknown_glyphs': 0}

        def reject_mutation(self, at, replacement, reason):
            end = at + len(replacement)
            original = self.payload[at:end]
            try:
                self.payload[at:end] = replacement
                with self.assertRaisesRegex(ValueError, reason):
                    check_ramdisk(self.payload, self.root)
            finally:
                self.payload[at:end] = original

        def test_verified_layout(self):
            self.assertEqual(check_ramdisk(self.payload, self.root)['size'], 33554432)

        def test_truncated_table(self):
            with self.assertRaisesRegex(ValueError, 'table or ADT extent'):
                check_ramdisk(self.payload[:0x2a8], self.root)

        def test_truncated_disk(self):
            with self.assertRaisesRegex(ValueError, 'exactly 32 MiB'):
                check_ramdisk(self.payload, self.root[:-1])

        def test_disk_beyond_memory(self):
            self.reject_mutation(0x40, struct.pack('<Q', 1), 'escapes the payload RAM window')

        def test_disagreeing_adt_range(self):
            start, length = struct.unpack_from('<2Q', self.payload, 0x20)
            key = self.payload.index(b'RAMDisk\0', start, start + length)
            self.reject_mutation(key + 36, bytes(8), 'ADT RAMDisk does not name')

        def test_read_write_root_argument(self):
            key = self.payload.index(b'rootrw=0', 0x48, 0x2a8)
            self.reject_mutation(key, b'rootrw=1', 'expected a read-only md0 root')

        def test_screen_cannot_claim_exit_by_itself(self):
            screen = 'RAMROOT USER: dynamic pid=2 ppid=1 images=37 libSystem=1\n'
            screen += 'RAMROOT USER: PASS dynamic pid=2\n'
            checks, identities = check_execution(screen, self.result, 38)
            self.assertFalse(checks['dynamic_exit_zero_verified_by_pid1'])
            self.assertIsNone(identities['dynamic_exit'])

        def test_static_exit_requires_static_entry(self):
            screen = 'RAMROOT USER: static child pid=3 exit=42 wait=2a00\n'
            checks, _ = check_execution(screen, self.result, 38)
            self.assertFalse(checks['static_child_exec_and_wait'])

        def test_loader_failure_overrides_clean_result(self):
            checks, _ = check_execution('Library not loaded: /usr/lib/example.dylib', self.result, 38)
            self.assertFalse(checks['no_visible_panic_or_loader_failure'])

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RamRootEvidence)
    return unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.output) else 1)
