#!/usr/bin/env python3
"""Summarize an already captured Duchamp UFS Perfetto trace offline.

The analyzer has no ADB, phone, MMIO, firmware, storage or partition interface.
It requires Perfetto's official Python package and writes one fail-closed JSON
report without changing the input trace.
"""

import argparse
import hashlib
import json
from pathlib import Path

from perfetto.trace_processor import TraceProcessor
from perfetto.protos.perfetto.trace import perfetto_trace_pb2


ACTIVITY_EVENTS = (
    "ufshcd_command",
    "scsi_dispatch_cmd_start",
    "scsi_dispatch_cmd_done",
)
OBSERVATION_EVENTS = (
    "swiotlb_bounced",
    "iommu_map",
    "iommu_unmap",
)
EXPECTED_EVENTS = ACTIVITY_EVENTS + OBSERVATION_EVENTS


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def query_rows(processor, sql):
    return [dict(row.__dict__) for row in processor.query(sql)]


def parse_ftrace_setup(trace):
    decoded = perfetto_trace_pb2.Trace()
    decoded.ParseFromString(trace.read_bytes())
    phases = []
    unknown = set()
    failed = set()
    exclusive_errors = set()
    atrace_errors = set()
    for packet in decoded.packet:
        if not packet.HasField("ftrace_stats"):
            continue
        stats = packet.ftrace_stats
        phase_name = stats.Phase.Name(stats.phase)
        phases.append(phase_name)
        unknown.update(stats.unknown_ftrace_events)
        failed.update(stats.failed_ftrace_events)
        if stats.exclusive_feature_error:
            exclusive_errors.add(stats.exclusive_feature_error)
        if stats.atrace_errors:
            atrace_errors.add(stats.atrace_errors)
    return {
        "phases": phases,
        "unknown_events": sorted(unknown),
        "failed_events": sorted(failed),
        "exclusive_feature_errors": sorted(exclusive_errors),
        "atrace_errors": sorted(atrace_errors),
    }


def stat_total(rows, name):
    return sum(row["value"] for row in rows if row["name"] == name)


def evaluate(counts, stats, setup, trace_unchanged):
    setup_error_count = stat_total(stats, "ftrace_setup_errors")
    setup_clean = (
        setup_error_count == 0
        and not setup["unknown_events"]
        and not setup["failed_events"]
        and not setup["exclusive_feature_errors"]
    )
    activity_observed = all(counts.get(name, 0) > 0 for name in ACTIVITY_EVENTS)
    if not setup_clean:
        outcome = "tracepoint_setup_failed"
    elif not activity_observed:
        outcome = "ufs_activity_not_observed"
    else:
        outcome = "ufs_activity_and_dma_route_observations_captured"
    return {
        "passed": trace_unchanged and setup_clean and activity_observed,
        "outcome": outcome,
        "trace_unchanged": trace_unchanged,
        "tracepoint_setup_clean": setup_clean,
        "ftrace_setup_error_count": setup_error_count,
        "ufs_activity_observed": activity_observed,
        "zero_is_valid_for_route_observers": list(OBSERVATION_EVENTS),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    trace = args.trace.resolve()
    output = args.output.resolve()
    if not trace.is_file():
        parser.error("trace does not exist")
    if output.exists():
        parser.error("preserve existing output")

    before = sha256(trace)
    setup = parse_ftrace_setup(trace)
    try:
        with TraceProcessor(trace=str(trace)) as processor:
            raw_counts = query_rows(
                processor,
                "SELECT name, COUNT(*) AS count FROM raw GROUP BY name ORDER BY name",
            )
            slices = query_rows(
                processor,
                "SELECT name, COUNT(*) AS count FROM slice GROUP BY name "
                "ORDER BY count DESC, name LIMIT 200",
            )
            stats = query_rows(
                processor,
                "SELECT name, value FROM stats WHERE value != 0 ORDER BY name",
            )
            metadata = query_rows(
                processor,
                "SELECT name, key_type, int_value, str_value FROM metadata "
                "ORDER BY name, str_value",
            )
    except Exception as error:
        parser.exit(1, f"Perfetto analysis failed: {error}\n")

    counts = {row["name"]: row["count"] for row in raw_counts}
    trace_unchanged = sha256(trace) == before
    evaluation = evaluate(counts, stats, setup, trace_unchanged)
    report = {
        "passed": evaluation["passed"],
        "evaluation": evaluation,
        "trace": {
            "bytes": trace.stat().st_size,
            "sha256": before,
            "unchanged": trace_unchanged,
        },
        "ftrace_setup": setup,
        "expected_event_counts": {
            name: counts.get(name, 0) for name in EXPECTED_EVENTS
        },
        "event_roles": {
            "required_activity_witnesses": list(ACTIVITY_EVENTS),
            "zero_permitted_observers": list(OBSERVATION_EVENTS),
        },
        "all_raw_event_counts": raw_counts,
        "slice_counts": slices,
        "nonzero_import_stats": stats,
        "metadata": metadata,
        "safety": {
            "offline_only": True,
            "adb_access": False,
            "phone_access": False,
            "storage_access": False,
            "mmio_access": False,
            "partition_access": False,
        },
        "scope": "offline Perfetto trace decoding; event presence alone does not prove physical XNU UFS safety",
        "evidence_limits": {
            "zero_route_events_only_mean_no_events_observed_when_setup_is_clean": True,
            "physical_dma_identity_or_secure_translation_proven": False,
            "xnu_phone_ufs_safe": False,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
