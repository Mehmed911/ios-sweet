#!/usr/bin/env python3
"""Capture positive per-thread IOMMU/SWIOTLB counters on Duchamp.

This uses temporary simpleperf events and fixed regular-file reads.  It stores
only host-side reports and does not modify tracefs, SELinux, the kernel,
firmware, phone files, partitions or MMIO.
"""

import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
import time


EVENTS = (
    "iommu:map",
    "iommu:unmap",
    "swiotlb:swiotlb_bounced",
)
READ_FILES = (
    "/system/apex/com.android.btservices.apex",
    "/system/apex/com.android.i18n.apex",
    "/system/apex/com.android.vndk.current.apex",
    "/system/apex/com.google.android.art.apex",
    "/system/apex/com.google.android.media.swcodec.apex",
)


def run(argv, timeout=30):
    return subprocess.run(
        argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=timeout,
    )


def decode(raw, label):
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeError as error:
        raise ValueError(f"{label} is not UTF-8") from error


def parse_rows(text):
    rows = []
    seen_events = set()
    for fields in csv.reader(io.StringIO(text)):
        if len(fields) < 5 or fields[4] not in EVENTS:
            continue
        seen_events.add(fields[4])
        if not fields[1].isdigit() or not fields[2].isdigit():
            raise ValueError("invalid simpleperf pid/tid")
        count = fields[3].strip().replace(",", "")
        if not count.isdigit():
            raise ValueError(f"invalid simpleperf count: {fields[3]}")
        if int(count) > 0:
            rows.append({
                "comm": fields[0],
                "pid": int(fields[1]),
                "tid": int(fields[2]),
                "count": int(count),
                "event": fields[4],
            })
    missing = sorted(set(EVENTS) - seen_events)
    if missing:
        raise ValueError("missing per-thread events: " + ", ".join(missing))
    rows.sort(key=lambda row: (row["event"], -row["count"], row["pid"], row["tid"]))
    return rows


def parse_iommu_format(text):
    fields = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("field:"):
            continue
        declaration = line.split(";", 1)[0][len("field:"):].strip()
        fields.append(declaration.rsplit(" ", 1)[-1])
    if not fields or "iova" not in fields or "paddr" not in fields:
        raise ValueError("unexpected iommu:map format")
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=12)
    parser.add_argument("--serial")
    args = parser.parse_args()
    if not args.adb.is_file():
        parser.error("ADB does not exist")
    if args.output.exists():
        parser.error("preserve existing output")
    if args.seconds < 8 or args.seconds > 30:
        parser.error("seconds must be between 8 and 30")

    devices_result = run([str(args.adb), "devices"])
    if devices_result.returncode:
        parser.error("adb devices failed")
    devices = [
        fields[0]
        for line in decode(devices_result.stdout, "adb devices").splitlines()[1:]
        if len(fields := line.split()) >= 2 and fields[1] == "device"
    ]
    serial = args.serial or (devices[0] if len(devices) == 1 else None)
    if serial is None or serial not in devices:
        parser.error(f"select one online device; found {len(devices)}")
    prefix = [str(args.adb), "-s", serial]
    device = decode(run(prefix + ["shell", "getprop", "ro.product.device"]).stdout,
                    "device")
    hardware = decode(run(prefix + ["shell", "getprop", "ro.boot.hardware"]).stdout,
                      "hardware")
    if (device, hardware) != ("duchamp", "mt6897"):
        parser.error(f"unexpected target {device}/{hardware}")

    format_result = run(prefix + [
        "shell", "su", "-c", "cat /sys/kernel/tracing/events/iommu/map/format"
    ])
    if format_result.returncode:
        parser.exit(1, "cannot read iommu:map format\n")
    format_text = decode(format_result.stdout, "iommu format")
    format_fields = parse_iommu_format(format_text)

    remote = (
        "simpleperf stat -a --per-thread --sort count --duration {} --csv -e {}"
        .format(args.seconds, ",".join(EVENTS))
    )
    process = subprocess.Popen(
        prefix + ["shell", "su", "-c", remote],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    reads = []
    try:
        time.sleep(2)
        for path in READ_FILES:
            started = time.monotonic()
            result = run(prefix + [
                "shell", "toybox", "dd", f"if={path}", "of=/dev/null",
                "bs=1048576", "status=none",
            ])
            reads.append({
                "path": path,
                "exit": result.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "stderr": decode(result.stderr, "dd stderr"),
            })
            if result.returncode:
                raise ValueError(f"read trigger failed: {path}")
        stdout, stderr = process.communicate(timeout=args.seconds + 15)
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
    if process.returncode:
        parser.exit(1, f"simpleperf/ADB exited {process.returncode}\n")
    output_text = "\n".join((
        decode(stdout, "simpleperf stdout"),
        decode(stderr, "simpleperf stderr"),
    ))
    positive = parse_rows(output_text)
    totals = {
        event: sum(row["count"] for row in positive if row["event"] == event)
        for event in EVENTS
    }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "iommu-map-format.txt").write_text(
        format_text + "\n", encoding="utf-8"
    )
    report = {
        "passed": all(row["exit"] == 0 for row in reads),
        "target": {"device": device, "hardware": hardware},
        "duration_seconds": args.seconds,
        "events": list(EVENTS),
        "positive_rows": positive,
        "positive_totals": totals,
        "iommu_map_tracepoint_fields": format_fields,
        "claims": {
            "swiotlb_bounce_observed": totals["swiotlb:swiotlb_bounced"] > 0,
            "iommu_activity_observed": totals["iommu:map"] > 0,
            "iommu_tracepoint_contains_device_identity": False,
            "iommu_events_attributed_to_ufs": False,
        },
        "reads": reads,
        "safety": {
            "temporary_perf_event_session": True,
            "regular_files_read_to_dev_null": True,
            "phone_file_write": False,
            "tracefs_control_write": False,
            "partition_access": False,
            "mmio_access": False,
            "firmware_call_issued": False,
            "kernel_module_loaded": False,
            "selinux_policy_changed": False,
        },
        "scope": (
            "positive per-thread system-wide counters; iommu:map has iova/paddr/size "
            "but no device field, so events are never promoted to UFS attribution"
        ),
    }
    (output / "result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
