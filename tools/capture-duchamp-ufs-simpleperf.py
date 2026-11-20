#!/usr/bin/env python3
"""Count Duchamp UFS/DMA tracepoints with Android simpleperf.

The counter session is temporary and system-wide.  Its workload only reads a
fixed allowlist of regular system files into /dev/null.  It does not write a
phone file, tracefs control, partition, MMIO register, firmware service,
kernel module or SELinux policy.
"""

import argparse
import csv
import io
import json
from pathlib import Path
import re
import subprocess
import time


EVENTS = (
    "ufs:ufshcd_command",
    "scsi:scsi_dispatch_cmd_start",
    "scsi:scsi_dispatch_cmd_done",
    "swiotlb:swiotlb_bounced",
    "iommu:map",
    "iommu:unmap",
)
ACTIVITY_EVENTS = EVENTS[1:3]
ROUTE_EVENTS = EVENTS[3:]
TIMER_HWIRQ = 27
UFS_HWIRQS = (200, 209, 210, 211, 212, 213, 214, 215, 216)
READ_FILES = (
    "/system/apex/com.android.btservices.apex",
    "/system/apex/com.android.i18n.apex",
    "/system/apex/com.android.vndk.current.apex",
    "/system/apex/com.google.android.art.apex",
    "/system/apex/com.google.android.media.swcodec.apex",
    "/system/framework/arm64/boot-framework.oat",
    "/system/framework/framework-res.apk",
    "/system/framework/framework.jar",
    "/system/framework/oat/arm64/services.odex",
    "/system/framework/services.jar",
    "/system_ext/framework/oat/arm64/miui-services.odex",
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


def online_devices(adb):
    result = run([str(adb), "devices"])
    if result.returncode:
        raise ValueError("adb devices failed")
    return [
        fields[0]
        for line in decode(result.stdout, "adb devices").splitlines()[1:]
        if len(fields := line.split()) >= 2 and fields[1] == "device"
    ]


def parse_counts(text):
    counts = {}
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 2 or row[1] not in EVENTS:
            continue
        raw = row[0].strip().replace(",", "")
        if not raw.isdigit():
            raise ValueError(f"unusable simpleperf count for {row[1]}: {row[0]}")
        if row[1] in counts:
            raise ValueError(f"duplicate simpleperf count: {row[1]}")
        counts[row[1]] = int(raw)
    missing = sorted(set(EVENTS) - set(counts))
    if missing:
        raise ValueError("missing simpleperf counts: " + ", ".join(missing))
    return counts


def parse_gic_interrupts(text):
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty /proc/interrupts capture")
    cpu_count = len(re.findall(r"\bCPU\d+\b", lines[0]))
    if not 1 <= cpu_count <= 256:
        raise ValueError("invalid CPU header in /proc/interrupts")
    rows = {}
    for line in lines[1:]:
        match = re.match(r"\s*(\d+):\s+(.*)", line)
        if not match:
            continue
        fields = match.group(2).split()
        if len(fields) < cpu_count + 4:
            continue
        counters = fields[:cpu_count]
        tail = fields[cpu_count:]
        if (not all(value.isdecimal() for value in counters)
                or tail[0] != "GICv3" or not tail[1].isdecimal()):
            continue
        hwirq = int(tail[1])
        if hwirq in rows:
            raise ValueError(f"duplicate GIC HWIRQ {hwirq}")
        rows[hwirq] = {
            "linux_irq": int(match.group(1)),
            "per_cpu": [int(value) for value in counters],
            "trigger": tail[2],
            "name": " ".join(tail[3:]),
        }
    return cpu_count, rows


def interrupt_deltas(before_text, after_text):
    before_cpus, before = parse_gic_interrupts(before_text)
    after_cpus, after = parse_gic_interrupts(after_text)
    if before_cpus != after_cpus:
        raise ValueError("CPU count changed during capture")
    expected = (TIMER_HWIRQ,) + UFS_HWIRQS
    missing = sorted(set(expected) - set(before) | set(expected) - set(after))
    if missing:
        raise ValueError("missing expected GIC HWIRQs: " + ", ".join(map(str, missing)))
    result = {}
    for hwirq in expected:
        old = before[hwirq]
        new = after[hwirq]
        if (old["linux_irq"], old["trigger"], old["name"]) != (
                new["linux_irq"], new["trigger"], new["name"]):
            raise ValueError(f"GIC HWIRQ {hwirq} identity changed")
        delta = [end - start for start, end in zip(old["per_cpu"], new["per_cpu"])]
        if any(value < 0 for value in delta):
            raise ValueError(f"GIC HWIRQ {hwirq} moved backwards")
        result[str(hwirq)] = {
            "linux_irq": new["linux_irq"],
            "trigger": new["trigger"],
            "name": new["name"],
            "per_cpu_delta": delta,
            "total_delta": sum(delta),
        }
    return before_cpus, result


def evaluate(counts, reads_ok, irq_deltas=None, baseline=False):
    irq_deltas = irq_deltas or {
        str(TIMER_HWIRQ): {"total_delta": 1},
        **{str(hwirq): {"total_delta": 1} for hwirq in UFS_HWIRQS},
    }
    scsi_activity = all(counts[event] > 0 for event in ACTIVITY_EVENTS)
    timer_activity = irq_deltas[str(TIMER_HWIRQ)]["total_delta"] > 0
    ufs_irq_total = sum(irq_deltas[str(hwirq)]["total_delta"] for hwirq in UFS_HWIRQS)
    ufs_activity = scsi_activity and ufs_irq_total > 0
    passed = timer_activity and (baseline or (reads_ok and ufs_activity))
    return {
        "passed": passed,
        "mode": "baseline" if baseline else "fixed-read-workload",
        "scsi_activity_observed": scsi_activity,
        "architected_timer_irq_observed": timer_activity,
        "ufs_irq_total_delta": ufs_irq_total,
        "ufs_activity_observed": ufs_activity,
        "ufshcd_tracepoint_observed": counts["ufs:ufshcd_command"] > 0,
        "route_observer_zero_is_a_valid_measurement": list(ROUTE_EVENTS),
        "swiotlb_transfer_observed": counts["swiotlb:swiotlb_bounced"] > 0,
        "iommu_map_observed": counts["iommu:map"] > 0,
        "iommu_unmap_observed": counts["iommu:unmap"] > 0,
        "iommu_event_device_attribution_available": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial")
    parser.add_argument("--seconds", type=int, default=12)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    if not args.adb.is_file():
        parser.error("ADB does not exist")
    if args.output.exists():
        parser.error("preserve existing output")
    if args.seconds < 8 or args.seconds > 30:
        parser.error("seconds must be between 8 and 30")

    devices = online_devices(args.adb)
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

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before_result = run(prefix + ["shell", "su", "-c", "cat /proc/interrupts"])
    if before_result.returncode:
        parser.exit(1, "cannot read /proc/interrupts before capture\n")
    before_interrupts = decode(before_result.stdout, "interrupts before")
    remote = "simpleperf stat -a --duration {} --csv -e {}".format(
        args.seconds, ",".join(EVENTS)
    )
    process = subprocess.Popen(
        prefix + ["shell", "su", "-c", remote],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    reads = []
    try:
        time.sleep(2)
        for path in (() if args.baseline else READ_FILES):
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

    stdout_text = decode(stdout, "simpleperf stdout")
    stderr_text = decode(stderr, "simpleperf stderr")
    (output / "simpleperf.stdout.txt").write_text(
        stdout_text + "\n", encoding="utf-8"
    )
    (output / "simpleperf.stderr.txt").write_text(
        stderr_text + ("\n" if stderr_text else ""), encoding="utf-8"
    )
    if process.returncode:
        parser.exit(1, f"simpleperf/ADB exited {process.returncode}\n")
    after_result = run(prefix + ["shell", "su", "-c", "cat /proc/interrupts"])
    if after_result.returncode:
        parser.exit(1, "cannot read /proc/interrupts after capture\n")
    after_interrupts = decode(after_result.stdout, "interrupts after")
    (output / "interrupts-before.txt").write_text(
        before_interrupts + "\n", encoding="utf-8"
    )
    (output / "interrupts-after.txt").write_text(
        after_interrupts + "\n", encoding="utf-8"
    )
    cpu_count, irq_deltas = interrupt_deltas(before_interrupts, after_interrupts)
    counts = parse_counts("\n".join((stdout_text, stderr_text)))
    evaluation = evaluate(
        counts,
        all(row["exit"] == 0 for row in reads),
        irq_deltas,
        args.baseline,
    )
    report = {
        "passed": evaluation["passed"],
        "target": {"device": device, "hardware": hardware},
        "duration_seconds": args.seconds,
        "mode": evaluation["mode"],
        "events": list(EVENTS),
        "counts": counts,
        "interrupts": {"cpu_count": cpu_count, "gic_hwirq_deltas": irq_deltas},
        "evaluation": evaluation,
        "reads": reads,
        "safety": {
            "temporary_perf_event_session": True,
            "regular_files_read_to_dev_null": not args.baseline,
            "phone_file_write": False,
            "tracefs_control_write": False,
            "partition_access": False,
            "mmio_access": False,
            "firmware_call_issued": False,
            "kernel_module_loaded": False,
            "selinux_policy_changed": False,
        },
        "scope": (
            "Android tracepoint counts during fixed regular-file reads; "
            "this does not prove XNU ownership or physical DMA identity"
        ),
    }
    (output / "result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
