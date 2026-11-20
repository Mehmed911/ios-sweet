#!/usr/bin/env python3
"""Tests for the bounded simpleperf UFS baseline comparison."""

import copy
import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/compare-duchamp-ufs-simpleperf.py"
SPEC = importlib.util.spec_from_file_location("ufs_simpleperf_compare", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def capture(mode, counts, ufs_irq):
    baseline = mode == "baseline"
    return {
        "passed": True,
        "mode": mode,
        "target": {"device": "duchamp", "hardware": "mt6897"},
        "duration_seconds": 12,
        "events": list(MODULE.EXPECTED_EVENTS),
        "counts": counts,
        "evaluation": {
            "architected_timer_irq_observed": True,
            "ufs_irq_total_delta": ufs_irq,
            "ufs_activity_observed": not baseline,
        },
        "reads": [] if baseline else [{"path": "/system/a", "exit": 0}],
        "safety": {
            "temporary_perf_event_session": True,
            "regular_files_read_to_dev_null": not baseline,
            "phone_file_write": False,
            "tracefs_control_write": False,
            "partition_access": False,
            "mmio_access": False,
            "firmware_call_issued": False,
            "kernel_module_loaded": False,
            "selinux_policy_changed": False,
        },
    }


class SimpleperfComparisonTests(unittest.TestCase):
    def setUp(self):
        self.base_counts = {event: 0 for event in MODULE.EXPECTED_EVENTS}
        self.base_counts.update({
            "scsi:scsi_dispatch_cmd_start": 10,
            "scsi:scsi_dispatch_cmd_done": 9,
            "iommu:map": 2,
        })
        self.work_counts = copy.deepcopy(self.base_counts)
        self.work_counts.update({
            "scsi:scsi_dispatch_cmd_start": 30,
            "scsi:scsi_dispatch_cmd_done": 29,
            "iommu:map": 7,
        })
        self.baseline = capture("baseline", self.base_counts, 3)
        self.workload = capture("fixed-read-workload", self.work_counts, 20)

    def test_valid_comparison_preserves_claim_boundaries(self):
        report = MODULE.compare(self.baseline, self.workload)
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["workload_minus_baseline"]["ufs_irq_total_delta"], 17
        )
        self.assertTrue(
            report["claims"]["android_ufs_scsi_and_irq_activity_correlated_with_fixed_reads"]
        )
        self.assertFalse(report["claims"]["iommu_events_attributed_to_ufs"])
        self.assertFalse(report["claims"]["physical_xnu_ufs_ready"])

    def test_missing_scsi_increase_is_rejected(self):
        workload = copy.deepcopy(self.workload)
        workload["counts"]["scsi:scsi_dispatch_cmd_start"] = 10
        with self.assertRaisesRegex(ValueError, "SCSI starts"):
            MODULE.compare(self.baseline, workload)

    def test_missing_irq_increase_is_rejected(self):
        workload = copy.deepcopy(self.workload)
        workload["evaluation"]["ufs_irq_total_delta"] = 3
        with self.assertRaisesRegex(ValueError, "UFS IRQ"):
            MODULE.compare(self.baseline, workload)

    def test_unsafe_capture_is_rejected(self):
        workload = copy.deepcopy(self.workload)
        workload["safety"]["tracefs_control_write"] = True
        with self.assertRaisesRegex(ValueError, "unsafe"):
            MODULE.compare(self.baseline, workload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
