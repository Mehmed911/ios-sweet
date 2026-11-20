#!/usr/bin/env python3
"""0BSD ensure a signalled Apple process cannot be reported as exit zero."""
from pathlib import Path
import runpy
import unittest
decode=runpy.run_path(str(Path(__file__).with_name('test-duchamp-ios-graphics-admission.py')))['terminal_status']


class Status(unittest.TestCase):
    def test_normal_zero(self):self.assertEqual(decode(0),dict(signal=0,exit_status=0,core_dumped=False))
    def test_normal_42(self):self.assertEqual(decode(42<<8)['exit_status'],42)
    def test_sigabrt_is_not_exit_zero(self):self.assertEqual(decode(6),dict(signal=6,exit_status=None,core_dumped=False))
    def test_core_flag(self):self.assertTrue(decode(6|128)['core_dumped'])
    def test_sigkill(self):self.assertIsNone(decode(9)['exit_status'])
    def test_stopped_not_terminal(self):
        with self.assertRaises(ValueError):decode(0x137f)
    def test_invalid_values(self):
        for v in [-1,65536,True,'6']:
            with self.assertRaises(ValueError):decode(v)


if __name__=='__main__':unittest.main(verbosity=2)
