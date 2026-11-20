#!/usr/bin/env python3
"""0BSD saved-guest heartbeat validation under delayed console observation."""
from pathlib import Path
import runpy
import unittest

valid=runpy.run_path(str(Path(__file__).with_name('verify-sweet-syslogd.py')))['healthy_heartbeats']


def trace(values,pid=5):
    return ''.join('heartbeat=%s syslogd_running=1 server=%d probes_stopped=1\n'%(n,pid) for n in values)


class Heartbeats(unittest.TestCase):
    def test_exact_original_pair(self):self.assertTrue(valid(trace([1,2]),5))
    def test_delayed_observation(self):self.assertTrue(valid(trace(range(1,19)),5))
    def test_missing_second(self):self.assertFalse(valid(trace([1]),5))
    def test_missing_first(self):self.assertFalse(valid(trace([2,3]),5))
    def test_gap(self):self.assertFalse(valid(trace([1,3]),5))
    def test_replayed_sequence(self):self.assertFalse(valid(trace([1,2,1,2]),5))
    def test_wrong_process(self):self.assertFalse(valid(trace([1,2],6),5))
    def test_out_of_order(self):self.assertFalse(valid(trace([2,1]),5))
    def test_unhealthy_later_sample(self):self.assertFalse(valid(trace([1,2])+trace([3]).replace('running=1','running=0'),5))


if __name__=='__main__':unittest.main(verbosity=2)
