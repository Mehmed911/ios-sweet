#!/usr/bin/env python3
"""Reject missing callbacks, incomplete databases and failed native display RPCs."""
import unittest
from duchamp_ui_readiness import registry,display

REGISTRY='''REGISTRY REBUILD RESULT callback=1 transport_error=0 rebuilt=1 code=0
REGISTRY AFTER sample=0 witnessed=1 status=256 complete=1
REGISTRY NATIVE COMPLETE PASS
READINESS DONE kind=registry status=0
'''
DISPLAY='''DISPLAY NATIVE REPLY sample=0 kr=0 values=1220.000,2712.000,3.000,60.000 flags=0,1 valid=1
DISPLAY NATIVE REPLY sample=1 kr=0 values=1220.000,2712.000,3.000,60.000 flags=0,1 valid=1
DISPLAY NATIVE QUERY PASS
READINESS DONE kind=display status=0
'''


class ReadinessTests(unittest.TestCase):
    def test_complete_state_requires_real_callback(self):
        self.assertTrue(registry(REGISTRY)['verified'])
        for old,new in [('callback=1','callback=0'),('transport_error=0','transport_error=1'),('code=0','code=-54')]:
            self.assertFalse(registry(REGISTRY.replace(old,new))['verified'])
    def test_incomplete_bitfield_cannot_be_promoted(self):
        self.assertFalse(registry(REGISTRY.replace('status=256','status=768'))['verified'])
        self.assertFalse(registry(REGISTRY.replace('status=256','status=0'))['verified'])
    def test_done_or_pass_without_operation_is_insufficient(self):
        self.assertFalse(registry('REGISTRY NATIVE COMPLETE PASS\nREADINESS DONE kind=registry status=0\n')['verified'])
        self.assertFalse(display('DISPLAY NATIVE QUERY PASS\nREADINESS DONE kind=display status=0\n')['verified'])
    def test_two_valid_native_display_replies(self):
        self.assertTrue(display(DISPLAY)['verified'])
        self.assertTrue(display(DISPLAY.replace(',60.000',',0.000'))['verified'])
        self.assertFalse(display(DISPLAY.replace('sample=1','sample=0'))['verified'])
    def test_mig_error_and_unchanged_outputs_fail(self):
        self.assertFalse(display(DISPLAY.replace('kr=0','kr=-300'))['verified'])
        self.assertFalse(display(DISPLAY.replace('1220.000','-1.000'))['verified'])
        self.assertFalse(display(DISPLAY.replace('flags=0,1','flags=255,255'))['verified'])
    def test_nonfinite_and_contradictory_exit_fail(self):
        self.assertFalse(display(DISPLAY.replace('1220.000','nan'))['verified'])
        self.assertFalse(display(DISPLAY+'READINESS DONE kind=display status=5\n')['verified'])
        self.assertFalse(registry(REGISTRY+'READINESS DONE kind=registry status=5\n')['verified'])
    def test_springboard_record_is_an_additional_gate(self):
        app='REGISTRY APP identifier=com.apple.springboard installed=1 placeholder=0 path=/System/Library/CoreServices/SpringBoard.app\nREGISTRY APP RECORD PASS\n'
        self.assertFalse(registry(REGISTRY,require_app=True)['verified'])
        self.assertTrue(registry(app+REGISTRY,require_app=True)['verified'])
        self.assertFalse(registry(app.replace('installed=1','installed=0')+REGISTRY,require_app=True)['verified'])
        self.assertFalse(registry(app.replace('SpringBoard.app','SpringBoardXapp')+REGISTRY,require_app=True)['verified'])


if __name__=='__main__':unittest.main()
