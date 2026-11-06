#!/usr/bin/env python3
"""Exercise dependency-audit failure gates without private Apple inputs."""
from pathlib import Path
import runpy
import struct
import tempfile
import unittest

AUDIT = runpy.run_path(str(Path(__file__).with_name('audit-duchamp-ui-runtime.py')))


def binary(imports=(), subtype=0):
    commands = []
    for name, weak in imports:
        encoded = name.encode() + b'\0'
        length = (24 + len(encoded) + 7) & ~7
        commands.append(struct.pack('<6I', 0x80000018 if weak else 0xc, length, 24, 0, 0, 0)
                        + encoded + bytes(length - 24 - len(encoded)))
    return struct.pack('<8I', 0xfeedfacf, 0x100000c, subtype, 2, len(commands),
                       sum(map(len, commands)), 0, 0) + b''.join(commands)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ui-audit-test-')
        self.root = Path(self.temp.name).resolve()
        for path in ('/usr/lib/dyld', '/usr/lib/libSystem.B.dylib'):
            self.put(path, binary())

    def tearDown(self):
        self.temp.cleanup()

    def put(self, guest, data):
        path = self.root / guest.lstrip('/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def audit(self, roots=None):
        return AUDIT['audit_entry'](roots or [self.root], '/bin/probe')

    def test_missing_strong_import_prevents_complete(self):
        self.put('/bin/probe', binary([('/usr/lib/absent.dylib', False)]))
        result = self.audit()
        self.assertFalse(result['complete'])
        self.assertIn('/usr/lib/absent.dylib', result['missing'])

    def test_weak_import_is_reported_without_compatibility_claim(self):
        self.put('/bin/probe', binary([('/usr/lib/absent.dylib', True)]))
        result = self.audit()
        self.assertTrue(result['complete'])
        self.assertEqual(len(result['weak_imports_not_followed']), 1)

    def test_conflicting_provider_bytes_prevent_complete(self):
        self.put('/bin/probe', binary())
        extra = self.root / 'second'
        (extra / 'bin').mkdir(parents=True)
        (extra / 'bin/probe').write_bytes(binary() + b'changed')
        result = self.audit([self.root, extra])
        self.assertFalse(result['complete'])
        self.assertIn('conflicting', result['invalid']['/bin/probe']['error'])

    def test_arm64e_is_not_treated_as_plain_arm64(self):
        self.put('/bin/probe', binary(subtype=2))
        result = self.audit()
        self.assertFalse(result['complete'])
        self.assertIn('plain-arm64', result['invalid']['/bin/probe']['error'])

    def test_unresolved_inherited_rpath_prevents_complete(self):
        self.put('/bin/probe', binary([('@rpath/unavailable.dylib', False)]))
        result = self.audit()
        self.assertFalse(result['complete'])
        self.assertIn('@rpath/unavailable.dylib', result['invalid'])

    def test_path_traversal_is_rejected(self):
        self.put('/bin/probe', binary([('/usr/../outside.dylib', False)]))
        result = self.audit()
        self.assertFalse(result['complete'])
        self.assertIn('/usr/../outside.dylib', result['invalid'])


if __name__ == '__main__':
    unittest.main()
