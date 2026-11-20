#!/usr/bin/env python3
"""Tests for the fail-closed Duchamp UFS Perfetto analyzer."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from perfetto.protos.perfetto.trace import perfetto_trace_pb2


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/analyze-duchamp-ufs-perfetto.py"
SPEC = importlib.util.spec_from_file_location("ufs_perfetto_analyzer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def clean_setup():
    return {
        "phases": ["FTRACE_STATUS_START_OF_TRACE", "FTRACE_STATUS_END_OF_TRACE"],
        "unknown_events": [],
        "failed_events": [],
        "exclusive_feature_errors": [],
        "atrace_errors": [],
    }


class UfsPerfettoAnalyzerTests(unittest.TestCase):
    def test_route_observers_may_be_zero_after_clean_setup(self):
        counts = {name: 1 for name in MODULE.ACTIVITY_EVENTS}
        counts.update({name: 0 for name in MODULE.OBSERVATION_EVENTS})
        result = MODULE.evaluate(counts, [], clean_setup(), True)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["outcome"],
            "ufs_activity_and_dma_route_observations_captured",
        )

    def test_unknown_events_fail_closed(self):
        setup = clean_setup()
        setup["unknown_events"] = ["ufs/ufshcd_command"]
        counts = {name: 0 for name in MODULE.EXPECTED_EVENTS}
        stats = [{"name": "ftrace_setup_errors", "value": 1}]
        result = MODULE.evaluate(counts, stats, setup, True)
        self.assertFalse(result["passed"])
        self.assertEqual(result["outcome"], "tracepoint_setup_failed")

    def test_missing_ufs_activity_is_not_a_success(self):
        counts = {name: 0 for name in MODULE.EXPECTED_EVENTS}
        result = MODULE.evaluate(counts, [], clean_setup(), True)
        self.assertFalse(result["passed"])
        self.assertEqual(result["outcome"], "ufs_activity_not_observed")

    def test_changed_trace_is_rejected(self):
        counts = {name: 1 for name in MODULE.ACTIVITY_EVENTS}
        result = MODULE.evaluate(counts, [], clean_setup(), False)
        self.assertFalse(result["passed"])

    def test_raw_proto_exposes_unknown_event_names(self):
        trace = perfetto_trace_pb2.Trace()
        packet = trace.packet.add()
        packet.ftrace_stats.phase = 1
        packet.ftrace_stats.unknown_ftrace_events.extend(
            ["ufs/ufshcd_command", "iommu/map"]
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "trace.pftrace"
            path.write_bytes(trace.SerializeToString())
            setup = MODULE.parse_ftrace_setup(path)
        self.assertEqual(
            setup["unknown_events"], ["iommu/map", "ufs/ufshcd_command"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
