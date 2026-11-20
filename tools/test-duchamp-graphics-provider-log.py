#!/usr/bin/env python3
"""0BSD: reject corrupted/false-success variants of an actual guest log."""
import argparse
from pathlib import Path
import unittest
from duchamp_graphics_provider import parse

ap=argparse.ArgumentParser();ap.add_argument('log',type=Path);a=ap.parse_args()
text=a.log.read_text()


class Contract(unittest.TestCase):
    def test_real_log(self): self.assertTrue(parse(text)['passed'])
    def test_unsupported_success(self):
        self.assertFalse(parse(text.replace('selector=4294967295 kr=0xe00002c7','selector=4294967295 kr=0x0'))['passed'])
    def test_null_client(self):
        row=parse(text)['surface_client'];self.assertIsNotNone(row)
        self.assertFalse(parse(text.replace('connection='+row[1],'connection=0x0'))['passed'])
    def test_wrong_dictionary(self):
        self.assertFalse(parse(text.replace('IOProviderClass=IOAcceleratorES','IOProviderClass=IOCoreSurfaceRoot'))['passed'])
    def test_false_gpu_claim(self): self.assertFalse(parse(text.replace('gpu_published=0','gpu_published=1'))['passed'])
    def test_missing_check(self): self.assertFalse(parse(text.replace('PROVIDER CHECK userclient-close passed=1\n',''))['passed'])
    def test_duplicate_check(self): self.assertFalse(parse(text+'PROVIDER CHECK userclient-close passed=1\n')['passed'])
    def test_privileged_probe(self): self.assertFalse(parse(text.replace('uid=501','uid=0'))['passed'])


unittest.main(argv=['test-duchamp-graphics-provider-log.py'])
