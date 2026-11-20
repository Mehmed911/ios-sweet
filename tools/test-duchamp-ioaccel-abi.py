#!/usr/bin/env python3
"""0BSD: offline consumer-bound tests; no fabricated original GPU responses."""
import json
from pathlib import Path
import random
import struct
import unittest
from duchamp_ioaccel_abi import (CaptureError, DESCRIPTOR_BYTES, OFFSET_CAPACITY,
    U64_MAX, STRUCT_SHAPES, assess_memory_claim, decode_descriptor, inspect_request)


def fixture(base=0x100000, count=2):
    # Deliberately synthetic decoder fixture, never installed into any guest.
    b = bytearray(DESCRIPTOR_BYTES)
    struct.pack_into('<Q', b, 0, base)
    struct.pack_into('<i', b, 0x14, count)
    b[0x18:0x1c] = b'abc\0'
    if 0 <= count <= OFFSET_CAPACITY:
        for i in range(count):
            struct.pack_into('<I', b, 0x58 + 4*i, 4*i)
    return b


class ConsumerTests(unittest.TestCase):
    def test_exact_size(self):
        self.assertEqual(decode_descriptor(fixture())['size'], 600)

    def test_short_and_long(self):
        for n in (0, 1, 599, 601, 4096):
            with self.subTest(n=n), self.assertRaises(CaptureError):
                decode_descriptor(bytes(n))

    def test_unaligned_capture_uses_bytes(self):
        b = b'x' + fixture() + b'y'
        self.assertEqual(decode_descriptor(memoryview(b)[1:-1])['base_raw'], 0x100000)

    def test_noncontiguous_capture(self):
        with self.assertRaises(CaptureError):
            decode_descriptor(memoryview(bytes(1200))[::2])

    def test_zero_count_no_addresses(self):
        self.assertEqual(decode_descriptor(fixture(count=0))['consumer_addresses'], [])

    def test_one_uses_base_not_offset(self):
        b = fixture(count=1);struct.pack_into('<I', b, 0x58, 0xffffffff)
        d = decode_descriptor(b)
        self.assertEqual(d['consumer_addresses'], [0x100000])
        self.assertEqual(d['offset_words'], [])

    def test_two_offsets(self):
        self.assertEqual(decode_descriptor(fixture())['consumer_addresses'], [0x100000, 0x100004])

    def test_available_capture_limit(self):
        d = decode_descriptor(fixture(count=128))
        self.assertEqual(len(d['offset_words']), 128)
        self.assertTrue(d['capture_capacity_is_not_producer_limit'])

    def test_invalid_counts(self):
        for count in (-1, -2147483648, 129, 2147483647):
            with self.subTest(count=count), self.assertRaises(CaptureError):
                decode_descriptor(fixture(count=count))

    def test_address_addition_wrap(self):
        with self.assertRaises(CaptureError):decode_descriptor(fixture(U64_MAX - 3))

    def test_four_byte_load_wrap(self):
        with self.assertRaises(CaptureError):decode_descriptor(fixture(U64_MAX, 1))

    def test_last_nonwrapping_load(self):
        self.assertEqual(decode_descriptor(fixture(U64_MAX - 3, 1))['consumer_addresses'], [U64_MAX - 3])

    def test_symbol_consumer_is_dlsym(self):
        d = decode_descriptor(fixture())
        self.assertEqual(d['dlsym_name_hex'], b'abc'.hex())
        self.assertTrue(d['text_extent'].startswith('UNKNOWN'))

    def test_unterminated_symbol_not_extended_into_offsets(self):
        b=fixture();b[0x18:0x58]=b'A'*64
        d=decode_descriptor(b)
        self.assertFalse(d['dlsym_terminated_in_prefix'])
        self.assertIsNone(d['dlsym_name_hex'])

    def test_opaque_fields_not_interpreted_as_pointers(self):
        b=fixture();b[8:16]=b'\xff'*8;struct.pack_into('<I',b,16,0xdeadbeef)
        d=decode_descriptor(b)
        self.assertEqual(d['opaque_08_0f'],'ff'*8)
        self.assertEqual(d['opaque_u32_10'],0xdeadbeef)
        self.assertEqual(d['consumer_addresses'],[0x100000,0x100004])

    def test_zero_reply_never_proves_compatibility(self):
        d=decode_descriptor(bytes(600))
        self.assertFalse(d['graphics_execution']);self.assertFalse(d['provider_compatible'])
        for key in ('ownership','mapping','synchronization'):self.assertEqual(d[key],'UNKNOWN')

    def test_random_bytes_no_address_access(self):
        rng=random.Random(20_066)
        for _ in range(1000):
            b=bytearray(rng.randbytes(600));struct.pack_into('<i',b,20,rng.randrange(129))
            try:d=decode_descriptor(b)
            except CaptureError:continue
            self.assertFalse(d['graphics_execution'])


class ShapeTests(unittest.TestCase):
    def test_known_shapes(self):
        for (kind, selector),(n,cap) in STRUCT_SHAPES.items():
            d=inspect_request(kind,selector,bytes(n),cap)
            self.assertEqual(d['status'],'STATIC_SHAPE_RECOGNIZED')
            self.assertFalse(d['graphics_execution'])

    def test_wrong_input_sizes(self):
        for (kind,sel),(n,cap) in STRUCT_SHAPES.items():
            with self.subTest(kind=kind,sel=sel),self.assertRaises(CaptureError):
                inspect_request(kind,sel,bytes(n+1),cap)

    def test_wrong_output_sizes(self):
        for (kind,sel),(n,cap) in STRUCT_SHAPES.items():
            with self.subTest(kind=kind,sel=sel),self.assertRaises(CaptureError):
                inspect_request(kind,sel,bytes(n),cap+1)

    def test_selector_seven_is_type_specific(self):
        with self.assertRaises(CaptureError):inspect_request(2,7,bytes(16),0)
        with self.assertRaises(CaptureError):inspect_request(1,7,b'',16)

    def test_other_types(self):
        for kind in (0,3,5,0xffffffff):
            with self.subTest(kind=kind),self.assertRaises(CaptureError):inspect_request(kind,0)

    def test_unknown_methods_are_explicit(self):
        for kind in (1,2,4):
            d=inspect_request(kind,0xffffffff)
            self.assertEqual(d['status'],'UNSUPPORTED_UNKNOWN_METHOD')
            self.assertFalse(d['provider_compatible'])

    def test_queue_shapes(self):
        for count in (0,1,2,128):
            b=bytearray(8+count*24);struct.pack_into('<i',b,4,count)
            d=inspect_request(4,1,b)
            self.assertEqual(d['record_count'],count)
            self.assertEqual(d['command_semantics'],'UNKNOWN')

    def test_queue_bad_sizes(self):
        for b in (b'',bytes(7),bytes(9),struct.pack('<Ii',0,1),struct.pack('<Ii',0,-1),struct.pack('<Ii',0,2147483647)):
            with self.subTest(n=len(b)),self.assertRaises(CaptureError):inspect_request(4,1,b)

    def test_queue_no_output(self):
        with self.assertRaises(CaptureError):inspect_request(4,1,bytes(8),1)

    def test_integer_contract(self):
        for x in (-1,True,1.0,'1',None,1<<64):
            with self.subTest(x=x),self.assertRaises(CaptureError):inspect_request(x,0)


class IsolationTests(unittest.TestCase):
    def assess(self,**overrides):
        args=dict(base=0x100000,size=16384,owner_pid=38,caller_pid=38,live=True,mapped=True,sync=True)
        args.update(overrides);return assess_memory_claim(**args)

    def test_positive_assertions_do_not_become_proof(self):
        d=self.assess();self.assertEqual(d['reasons'],['PRODUCER_CONTRACT_UNVERIFIED'])
        self.assertFalse(d['graphics_execution'])

    def test_foreign_owner(self):self.assertIn('OWNER_MISMATCH',self.assess(caller_pid=39)['reasons'])
    def test_zero_owner(self):self.assertIn('OWNER_MISMATCH',self.assess(owner_pid=0)['reasons'])
    def test_stale_handle(self):self.assertIn('STALE_OR_UNKNOWN_HANDLE',self.assess(live=False)['reasons'])
    def test_missing_mapping(self):self.assertIn('MAPPING_UNVERIFIED',self.assess(mapped=None)['reasons'])
    def test_missing_sync(self):self.assertIn('SYNCHRONIZATION_UNVERIFIED',self.assess(sync=None)['reasons'])
    def test_integer_is_not_proof(self):
        d=self.assess(live=1,mapped=1,sync=1)
        self.assertEqual(len(d['reasons']),4)
    def test_empty_range(self):self.assertIn('INVALID_OR_WRAPPING_RANGE',self.assess(size=0)['reasons'])
    def test_range_overflow(self):self.assertIn('INVALID_OR_WRAPPING_RANGE',self.assess(base=U64_MAX)['reasons'])


if __name__=='__main__':unittest.main(verbosity=2)
