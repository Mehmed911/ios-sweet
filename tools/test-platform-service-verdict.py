#!/usr/bin/env python3
"""Requested UI probes must contribute to the overall batch verdict."""
from pathlib import Path
import runpy
import unittest

verdict=runpy.run_path(str(Path(__file__).with_name('test-duchamp-platform-services.py')))['batch_passed']
UI={'runningboardd_native_identity':True,'backboardd_native_identity':True,
    'six_five_second_health_checks':True,'native_reply_after_ui':True}


class VerdictTests(unittest.TestCase):
    def test_core_only_does_not_require_ui(self):
        self.assertTrue(verdict({'core':True},{},False))
    def test_requested_ui_cannot_be_omitted(self):
        self.assertFalse(verdict({'core':True},{},True))
    def test_each_ui_failure_blocks_success(self):
        for name in UI:
            changed={**UI,name:False}
            self.assertFalse(verdict({'core':True},changed,True))
    def test_all_checks_must_be_real_true(self):
        self.assertTrue(verdict({'core':True},UI,True))
        self.assertFalse(verdict({'core':1},UI,True))
        self.assertFalse(verdict({},UI,True))


if __name__=='__main__':unittest.main()
