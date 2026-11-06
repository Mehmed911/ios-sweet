#!/usr/bin/env python3
"""Check that analysis exports cannot become falsely approved standalone inputs."""
from pathlib import Path
import hashlib
import json
import runpy
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import uuid

AUDIT = runpy.run_path(str(Path(__file__).with_name('audit-duchamp-cache-exports.py')))
LOADER = AUDIT['loader_metadata']
REUSE = runpy.run_path(str(Path(__file__).with_name('extract-duchamp-systemos-cache.py')))['verify_reused_component']


class ExportGateTests(unittest.TestCase):
    def make(self, target, broken_range=False):
        command = struct.pack('<II16s4Q4I', 0x19, 72, b'__DATA', 0x180000000, 4096,
                              256, 8192 if broken_range else 8, 3, 3, 0, 0)
        header = struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 6, 1, len(command), 0x02100085, 0)
        return header + command + bytes(256 - len(header) - len(command)) + struct.pack('<Q', target)

    def inspect(self, data):
        with tempfile.TemporaryDirectory(prefix='cache-export-test-') as directory:
            path = Path(directory) / 'sample'
            path.write_bytes(data)
            return LOADER(path)

    def test_external_pointer_without_fixups_is_blocked(self):
        result = self.inspect(self.make(0x190000000))
        self.assertTrue(result['standalone_blockers'])
        self.assertFalse(result['standalone_payload_allowed'])

    def test_internal_pointer_is_not_mislabeled_external(self):
        result = self.inspect(self.make(0x180000008))
        self.assertFalse(result['sampled_external_cache_pointers'])
        self.assertFalse(result['standalone_blockers'])
        self.assertFalse(result['standalone_payload_allowed'])

    def test_absence_of_sampled_pointer_is_not_runtime_approval(self):
        result = self.inspect(self.make(0))
        self.assertFalse(result['standalone_payload_allowed'])

    def test_out_of_file_segment_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(self.make(0, broken_range=True))

    def test_failed_closure_exit_is_propagated_and_report_kept(self):
        with tempfile.TemporaryDirectory(prefix='cache-closure-failure-') as directory:
            root = Path(directory)
            exports = root / 'derived'
            exports.mkdir()
            images = []
            for index, name in enumerate(AUDIT['NAMES']):
                ident = uuid.UUID(int=index + 1)
                data = bytearray(self.make(0))
                data[16:24] = struct.pack('<II', 2, 96)
                data[104:128] = struct.pack('<II', 0x1b, 24) + ident.bytes
                (exports / name).write_bytes(data)
                images.append(dict(name='/System/Library/PrivateFrameworks/' + name + '.framework/' + name,
                                   uuid=str(ident).upper()))
            cache = root / 'cache.json'
            cache.write_text(json.dumps(dict(uuid='E5420DB3-30D0-33AA-8B7E-05B5038BB46D',
                magic='dyld_v1   arm64', dylibs=images)))
            output = root / 'audit'
            argv = ['audit', '--cache-info', str(cache), '--exports', str(exports), '--output', str(output)]
            with mock.patch.object(sys, 'argv', argv), mock.patch.object(subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], 1, stdout='closure incomplete')), mock.patch('builtins.print'):
                status = AUDIT['main']()
            self.assertEqual(status, 1)
            self.assertEqual(json.loads((output / 'summary.json').read_text())['closure_exit_code'], 1)

    def test_same_size_corruption_is_rejected_before_reuse(self):
        with tempfile.TemporaryDirectory(prefix='cache-corruption-') as directory:
            path = Path(directory) / 'component'
            original = b'original'
            path.write_bytes(b'corrupt!')
            manifest = dict(files={'component': dict(bytes=len(original), sha256=hashlib.sha256(original).hexdigest())})
            with self.assertRaises(SystemExit):
                REUSE(path, 'component', len(original), manifest)


if __name__ == '__main__':
    unittest.main()
