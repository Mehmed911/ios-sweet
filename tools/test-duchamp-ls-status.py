#!/usr/bin/env python3
"""Regression: a real 0x300 LS response is transport success, seeding incomplete."""
import unittest
from duchamp_ls_status import parse


def response(value):
    return ('LSD NATIVE STATUS REPLY status=%d\n'
        'LSD NATIVE QUERY RESULT reply=1 error=0 status=%d\n'
        'LSD NATIVE WRAPPER status=%d matches=1\n'
        'LSD NATIVE TRANSPORT PASS status=%d\n')%((value,)*4)


class StatusTests(unittest.TestCase):
    def test_observed_0x300_is_not_an_osstatus_failure(self):
        result=parse(response(768))
        self.assertTrue(result['transport_verified']);self.assertTrue(result['database_seeded'])
        self.assertFalse(result['database_seeding_complete'])
    def test_seed_complete_is_distinct(self):
        self.assertTrue(parse(response(256))['database_seeding_complete'])
    def test_zero_wrapper_without_reply_is_not_evidence(self):
        self.assertFalse(parse('LSD NATIVE WRAPPER status=0 matches=1\n')['transport_verified'])
    def test_conflicting_values_are_rejected(self):
        self.assertFalse(parse(response(768).replace('WRAPPER status=768','WRAPPER status=256'))['transport_verified'])
    def test_out_of_range_is_rejected(self):
        self.assertFalse(parse(response(1<<32))['transport_verified'])
    def test_error_or_duplicate_reply_is_rejected(self):
        for text in (response(768)+'LSD NATIVE QUERY ERROR invalid\n',response(768)*2):
            self.assertFalse(parse(text)['transport_verified'])


if __name__=='__main__':unittest.main()
