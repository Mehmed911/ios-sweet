#!/usr/bin/env python3
"""Tests for the Duchamp simpleperf UFS tracepoint collector."""

import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/capture-duchamp-ufs-simpleperf.py"
SPEC = importlib.util.spec_from_file_location("ufs_simpleperf", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class UfsSimpleperfTests(unittest.TestCase):
    def test_parse_counts(self):
        text = "\n".join(
            f"{index},{event},0.0,/sec,"
            for index, event in enumerate(MODULE.EVENTS, 1)
        )
        counts = MODULE.parse_counts(text)
        self.assertEqual(counts["ufs:ufshcd_command"], 1)
        self.assertEqual(counts["iommu:unmap"], len(MODULE.EVENTS))

    def test_zero_route_events_are_valid_when_ufs_is_active(self):
        counts = {event: 1 for event in MODULE.EVENTS}
        counts.update({event: 0 for event in MODULE.ROUTE_EVENTS})
        result = MODULE.evaluate(counts, True)
        self.assertTrue(result["passed"])
        self.assertFalse(result["swiotlb_transfer_observed"])
        self.assertFalse(result["iommu_map_observed"])

    def test_missing_ufs_activity_fails_closed(self):
        counts = {event: 0 for event in MODULE.EVENTS}
        self.assertFalse(MODULE.evaluate(counts, True)["passed"])

    def test_failed_read_fails_closed(self):
        counts = {event: 1 for event in MODULE.EVENTS}
        counts.update({event: 0 for event in MODULE.ROUTE_EVENTS})
        self.assertFalse(MODULE.evaluate(counts, False)["passed"])

    def test_baseline_only_requires_timer_progress(self):
        counts = {event: 0 for event in MODULE.EVENTS}
        result = MODULE.evaluate(counts, True, baseline=True)
        self.assertTrue(result["passed"])
        self.assertEqual(result["mode"], "baseline")

    def test_interrupt_parser_matches_timer_and_ufs(self):
        header = "           CPU0       CPU1"
        def capture(value):
            rows = [f" 20: {value:10d} {value:10d} GICv3  27 Level arch_timer"]
            rows.extend(
                f"{hwirq}: {value:10d} {value:10d} GICv3 {hwirq:3d} Level ufshcd"
                for hwirq in MODULE.UFS_HWIRQS
            )
            return "\n".join((header, *rows))
        cpus, deltas = MODULE.interrupt_deltas(capture(10), capture(12))
        self.assertEqual(cpus, 2)
        self.assertEqual(deltas["27"]["total_delta"], 4)
        self.assertEqual(deltas["216"]["total_delta"], 4)

    def test_missing_counter_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing simpleperf counts"):
            MODULE.parse_counts("1,ufs:ufshcd_command,0.0,/sec,")


if __name__ == "__main__":
    unittest.main(verbosity=2)
