#!/usr/bin/env python3
"""Capture selected UFS/DMA tracepoints through Android's Perfetto service.

The phone workload consists only of reading fixed regular system files into
``/dev/null``.  The Perfetto stream and all metadata are written on the host.
No phone file, partition, MMIO register, firmware service or kernel policy is
written by this tool.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


EVENTS = (
    "ufs/ufshcd_command",
    "swiotlb/swiotlb_bounced",
    "iommu/map",
    "iommu/unmap",
    "scsi/scsi_dispatch_cmd_start",
    "scsi/scsi_dispatch_cmd_done",
)
READ_FILES = (
    "/system/framework/arm64/boot-framework.oat",
    "/system/framework/framework-res.apk",
    "/system/framework/framework.jar",
    "/system/framework/oat/arm64/apex@com.android.wifi@javalib@service-wifi.jar@classes.odex",
    "/system/framework/oat/arm64/services.odex",
    "/system/framework/services.jar",
    "/system_ext/framework/oat/arm64/miui-services.odex",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, timeout=20):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial")
    parser.add_argument("--seconds", type=int, default=12)
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
    trace = output / "ufs-runtime.pftrace"
    adb_stderr = output / "adb.stderr.txt"
    # Remote stderr carries Perfetto's text log; discard it so stdout remains
    # a pure protobuf trace.  No remote output path is used.
    remote = "perfetto -t {}s -b 16mb -o - {} 2>/dev/null".format(
        args.seconds, " ".join(EVENTS)
    )
    reads = []
    with trace.open("wb") as trace_file, adb_stderr.open("wb") as stderr_file:
        process = subprocess.Popen(
            prefix + ["exec-out", "sh", "-c", remote],
            stdout=trace_file,
            stderr=stderr_file,
        )
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
            process.wait(timeout=args.seconds + 15)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    if process.returncode:
        parser.exit(1, f"Perfetto/ADB exited {process.returncode}\n")
    report = {
        "passed": trace.stat().st_size > 0 and all(row["exit"] == 0 for row in reads),
        "target": {"device": device, "hardware": hardware},
        "events": list(EVENTS),
        "duration_seconds": args.seconds,
        "trace": {
            "bytes": trace.stat().st_size,
            "sha256": sha256(trace),
        },
        "reads": reads,
        "safety": {
            "regular_files_read_to_dev_null": True,
            "phone_file_write": False,
            "partition_access": False,
            "mmio_access": False,
            "firmware_call_issued": False,
            "kernel_module_loaded": False,
            "selinux_policy_changed": False,
        },
        "scope": "Android Perfetto trace and regular-file reads only; no XNU or physical-UFS authorization claim",
    }
    (output / "capture.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
