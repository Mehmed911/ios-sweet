#!/usr/bin/env python3
"""0BSD malformed-image and closure tests; no execution or device access."""
from pathlib import Path
import struct
import tempfile
import unittest
from duchamp_macho_preflight import inspect, closure, guest_path


def command(kind, text, offset=24):
    raw = text.encode()+b'\0'
    size = (offset+len(raw)+7)&~7
    return struct.pack('<3I', kind, size, offset).ljust(offset,b'\0')+raw.ljust(size-offset,b'\0')


def image(commands=(), flags=0, cpu=0x100000c, subtype=0):
    body = b''.join(commands)
    return struct.pack('<8I',0xfeedfacf,cpu,subtype,2,len(commands),len(body),flags,0)+body


class Preflight(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='duchamp-macho-audit-')
        self.root=Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self,data):
        p=self.root/'input';p.write_bytes(data);return inspect(p)

    def test_valid_dependencies_and_weak(self):
        r=self.parse(image([command(0xc,'/lib/a'),command(0x80000018,'/lib/weak')]))
        self.assertEqual(r['dependencies'],[dict(path='/lib/a',weak=False),dict(path='/lib/weak',weak=True)])
        self.assertFalse(r['signature_authenticated'])

    def test_short_header(self):
        with self.assertRaises(ValueError):self.parse(b'\0'*31)

    def test_wrong_architecture(self):
        for data in [image(cpu=7),image(subtype=2)]:
            with self.assertRaises(ValueError):self.parse(data)

    def test_command_count(self):
        data=bytearray(image());struct.pack_into('<I',data,16,4097)
        with self.assertRaises(ValueError):self.parse(data)

    def test_declared_command_extent(self):
        data=bytearray(image());struct.pack_into('<I',data,20,8)
        with self.assertRaises(ValueError):self.parse(data)

    def test_zero_or_unaligned_command(self):
        for n in (0,7,12):
            data=bytearray(image([struct.pack('<2I',0xc,n)]))
            with self.assertRaises(ValueError):self.parse(data)

    def test_unterminated_string(self):
        data=bytearray(image([command(0xc,'/lib/a')]));data[56:]=b'x'*(len(data)-56)
        with self.assertRaises(ValueError):self.parse(data)

    def test_offset_into_command_header(self):
        data=bytearray(image([command(0xc,'/lib/a')]));struct.pack_into('<I',data,40,8)
        with self.assertRaises(ValueError):self.parse(data)

    def test_string_offset_beyond_command(self):
        data=bytearray(image([command(0xc,'/lib/a')]));struct.pack_into('<I',data,40,1000)
        with self.assertRaises(ValueError):self.parse(data)

    def test_uncovered_commands(self):
        data=bytearray(image([command(0xc,'/lib/a')]));struct.pack_into('<I',data,16,0)
        with self.assertRaises(ValueError):self.parse(data)

    def test_linkedit_out_of_bounds(self):
        with self.assertRaises(ValueError):self.parse(image([struct.pack('<4I',0x80000034,16,500,40)]))

    def test_segment_overflow(self):
        seg=struct.pack('<II16sQQQQIIII',0x19,72,b'__DATA',2**64-1,2,0,0,3,3,0,0)
        with self.assertRaises(ValueError):self.parse(image([seg]))

    def test_cache_flag_not_standalone(self):
        p=self.root/'a';p.write_bytes(image(flags=0x80000000))
        r=closure('/a',lambda n:p)
        self.assertFalse(r['static_closure_complete'])
        self.assertIn('MH_DYLIB_IN_CACHE',r['invalid']['/a'])

    def test_missing_cache_image_stays_missing(self):
        r=closure('/a',lambda n:None,{'/a'})
        self.assertFalse(r['static_closure_complete'])
        self.assertTrue(r['missing'][0]['in_host_cache_inventory'])

    def test_weak_missing_does_not_fail_strong_closure(self):
        p=self.root/'a';p.write_bytes(image([command(0x80000018,'/weak')]))
        r=closure('/a',lambda n:p if n=='/a' else None)
        self.assertTrue(r['static_closure_complete'])
        self.assertFalse(r['execution_proven'])

    def test_required_missing_fails(self):
        p=self.root/'a';p.write_bytes(image([command(0xc,'/required')]))
        r=closure('/a',lambda n:p if n=='/a' else None)
        self.assertFalse(r['static_closure_complete'])

    def test_cycle_terminates(self):
        a=self.root/'a';b=self.root/'b'
        a.write_bytes(image([command(0xc,'/b')]));b.write_bytes(image([command(0xc,'/a')]))
        r=closure('/a',lambda n:{'/a':a,'/b':b}.get(n))
        self.assertTrue(r['static_closure_complete']);self.assertEqual(len(r['files']),2)

    def test_inherited_runpath_is_unknown(self):
        p=self.root/'a';p.write_bytes(image([command(0xc,'@rpath/F')]))
        r=closure('/a',lambda n:p if n=='/a' else None)
        self.assertFalse(r['static_closure_complete']);self.assertIn('rpath resolution',r['invalid']['@rpath/F'])

    def test_weak_runpath_does_not_claim_required_dependency(self):
        p=self.root/'a';p.write_bytes(image([command(0x80000018,'@rpath/F')]))
        r=closure('/a',lambda n:p if n=='/a' else None)
        self.assertTrue(r['static_closure_complete']);self.assertFalse(r['execution_proven'])

    def test_unknown_required_command_denied(self):
        with self.assertRaises(ValueError):self.parse(image([struct.pack('<2I',0x80009999,8)]))

    def test_unsafe_paths(self):
        for p in ['relative','/a/../b','/a\\b','/a\0b']:
            with self.assertRaises(ValueError):guest_path(p)


if __name__=='__main__':unittest.main(verbosity=2)
