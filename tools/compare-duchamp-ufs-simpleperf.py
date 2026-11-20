#!/usr/bin/env python3
"""Compare bounded Android UFS tracepoint baseline and read workload reports."""

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_EVENTS = (
    "ufs:ufshcd_command",
    "scsi:scsi_dispatch_cmd_start",
    "scsi:scsi_dispatch_cmd_done",
    "swiotlb:swiotlb_bounced",
    "iommu:map",
    "iommu:unmap",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def receipt(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def validate(report, mode):
    require(report.get("passed") is True, f"{mode} capture did not pass")
    require(report.get("mode") == mode, f"unexpected {mode} mode")
    require(report.get("target") == {"device": "duchamp", "hardware": "mt6897"},
            f"unexpected {mode} target")
    require(tuple(report.get("events", ())) == EXPECTED_EVENTS,
            f"unexpected {mode} event list")
    counts = report.get("counts", {})
    require(set(counts) == set(EXPECTED_EVENTS), f"incomplete {mode} counters")
    require(all(isinstance(value, int) and value >= 0 for value in counts.values()),
            f"invalid {mode} counter")
    evaluation = report.get("evaluation", {})
    require(evaluation.get("architected_timer_irq_observed") is True,
            f"timer IRQ did not progress in {mode}")
    safety = report.get("safety", {})
    require(safety.get("temporary_perf_event_session") is True,
            f"{mode} did not use temporary perf events")
    for key in ("phone_file_write", "tracefs_control_write", "partition_access",
                "mmio_access", "firmware_call_issued", "kernel_module_loaded",
                "selinux_policy_changed"):
        require(safety.get(key) is False, f"unsafe {mode} action: {key}")
    return counts, evaluation


def compare(baseline, workload):
    baseline_counts, baseline_eval = validate(baseline, "baseline")
    workload_counts, workload_eval = validate(workload, "fixed-read-workload")
    require(baseline["duration_seconds"] == workload["duration_seconds"],
            "capture durations differ")
    require(workload["safety"].get("regular_files_read_to_dev_null") is True,
            "workload was not fixed regular-file reads")
    require(len(workload.get("reads", ())) >= 1, "workload has no reads")
    require(all(row.get("exit") == 0 for row in workload["reads"]),
            "workload read failed")
    require(workload_eval.get("ufs_activity_observed") is True,
            "workload UFS activity missing")

    deltas = {
        event: workload_counts[event] - baseline_counts[event]
        for event in EXPECTED_EVENTS
    }
    ufs_irq_delta = (
        workload_eval["ufs_irq_total_delta"] - baseline_eval["ufs_irq_total_delta"]
    )
    require(deltas["scsi:scsi_dispatch_cmd_start"] > 0,
            "workload did not increase SCSI starts")
    require(deltas["scsi:scsi_dispatch_cmd_done"] > 0,
            "workload did not increase SCSI completions")
    require(ufs_irq_delta > 0, "workload did not increase UFS IRQ delivery")

    return {
        "passed": True,
        "duration_seconds_each": baseline["duration_seconds"],
        "baseline_counts": baseline_counts,
        "workload_counts": workload_counts,
        "workload_minus_baseline": {
            "event_counts": deltas,
            "ufs_irq_total_delta": ufs_irq_delta,
        },
        "claims": {
            "android_arch_timer_irq_delivery_observed": True,
            "android_ufs_scsi_and_irq_activity_correlated_with_fixed_reads": True,
            "swiotlb_bounce_not_observed_in_either_window": (
                baseline_counts["swiotlb:swiotlb_bounced"] == 0
                and workload_counts["swiotlb:swiotlb_bounced"] == 0
            ),
            "system_wide_iommu_activity_observed": (
                baseline_counts["iommu:map"] > 0
                or workload_counts["iommu:map"] > 0
            ),
            "iommu_events_attributed_to_ufs": False,
            "physical_dma_identity_or_secure_translation_proven": False,
            "gic_or_firmware_ownership_for_xnu_proven": False,
            "xnu_phone_timer_irq_delivery_proven": False,
            "physical_xnu_ufs_ready": False,
        },
        "safety": {
            "offline_comparison_only": True,
            "phone_access": False,
            "storage_access": False,
            "partition_access": False,
            "mmio_access": False,
        },
        "scope": (
            "comparison of saved Android simpleperf counters and GIC IRQ deltas; "
            "IOMMU map events lack a device field and are not attributed to UFS"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    workload = json.loads(args.workload.read_text(encoding="utf-8"))
    try:
        report = compare(baseline, workload)
    except ValueError as error:
        parser.exit(1, f"comparison failed: {error}\n")
    report["inputs"] = {
        "baseline": receipt(args.baseline.resolve()),
        "workload": receipt(args.workload.resolve()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
