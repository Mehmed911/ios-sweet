#!/usr/bin/env python3
"""Collect and verify read-only MT6897 runtime evidence through ADB shell.

Only ``getprop``, ``cat`` and ``readlink`` are issued to an already connected
Android device.  The tool never requests root, writes a device file, invokes
fastboot, or accesses a partition.  Its positive result describes Android's
current GIC/timer/UFS routing only; it does not authorize XNU MMIO or DMA.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time


EXPECTED_DTB_SHA256 = (
    "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
)

PROBES = {
    "iomem": ("exec-out", "cat", "/proc/iomem"),
    "live_fdt": ("exec-out", "cat", "/sys/firmware/fdt"),
    "clocksource": (
        "exec-out",
        "cat",
        "/sys/devices/system/clocksource/clocksource0/current_clocksource",
    ),
    "clockevent": (
        "exec-out",
        "cat",
        "/sys/devices/system/clockevents/clockevent0/current_device",
    ),
    "ufs_driver": (
        "shell",
        "readlink",
        "-f",
        "/sys/devices/platform/soc/112b0000.ufshci/driver",
    ),
    "ufs_iommu_group": (
        "shell",
        "readlink",
        "-f",
        "/sys/devices/platform/soc/112b0000.ufshci/iommu_group",
    ),
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_live_parser(repo):
    path = repo / "tools/report-duchamp-mt6897-live-runtime.py"
    spec = importlib.util.spec_from_file_location("duchamp_live_runtime", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load runtime parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_command(argv, runner=subprocess.run):
    try:
        return runner(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"adb command timed out: {argv[1:3]}") from error


def probe_result(process):
    combined = process.stdout + b"\n" + process.stderr
    lowered = combined.lower()
    if b"permission denied" in lowered:
        status = "permission-denied"
    elif b"no such file" in lowered or b"can't open" in lowered:
        status = "unavailable"
    elif process.returncode != 0:
        status = "unavailable"
    elif process.stdout:
        status = "readable"
    else:
        status = "empty"
    return {
        "status": status,
        "readable": status == "readable",
        "returncode": process.returncode,
        "stdout_bytes": len(process.stdout),
        "stdout_sha256": sha256(process.stdout),
    }


def decode(raw, label):
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeError as error:
        raise ValueError(f"{label} is not UTF-8 text") from error


def online_devices(adb, runner=subprocess.run):
    process = run_command([str(adb), "devices"], runner)
    if process.returncode:
        raise ValueError("adb devices failed: " + decode(process.stderr, "adb stderr"))
    devices = []
    for line in decode(process.stdout, "adb devices").splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "device":
            devices.append(fields[0])
    return devices


def validate_boot_devices(value):
    devices = [entry for entry in value.split(",") if entry]
    required = {"soc/112b0000.ufshci", "112b0000.ufshci"}
    if not required.issubset(devices):
        raise ValueError(f"boot-device property does not identify Duchamp UFS: {devices}")
    return devices


def adb_read(adb, serial, command, runner=subprocess.run, required=True):
    allowed = command[:2] in {
        ("shell", "getprop"),
        ("shell", "readlink"),
        ("exec-out", "cat"),
    }
    if not allowed or any(token in command for token in ("su", "dd", "push", "pull")):
        raise ValueError(f"refusing non-read-only adb command: {command}")
    process = run_command([str(adb), "-s", serial, *command], runner)
    if required and process.returncode:
        error = decode(process.stderr, "adb stderr")
        raise ValueError(f"required adb read failed: {command}: {error}")
    return process


def expected_interrupts(reference_dtb, repo, runtime):
    raw = reference_dtb.read_bytes()
    if sha256(raw) != EXPECTED_DTB_SHA256:
        raise ValueError("reference DTB is not the pinned Duchamp capture")
    parser = runtime.load_fdt_parser(repo)
    tree = parser.Fdt(raw)
    if tree.nodes["/"].strings("model") != ["MT6897"]:
        raise ValueError("reference DTB model is not MT6897")
    timer = tree.nodes.get("/timer")
    ufs = tree.nodes.get("/soc/ufshci@112b0000")
    if timer is None or ufs is None:
        raise ValueError("reference DTB lacks timer or UFS")
    timer_hwirqs = []
    for entry in tree.interrupts(timer):
        args = entry["args"]
        if len(args) != 4 or args[0] != 1:
            raise ValueError(f"unsupported timer interrupt tuple: {args}")
        timer_hwirqs.append(args[1] + 16)
    ufs_hwirqs = []
    for entry in tree.interrupts(ufs):
        args = entry["args"]
        if len(args) != 4 or args[0] != 0:
            raise ValueError(f"unsupported UFS interrupt tuple: {args}")
        ufs_hwirqs.append(args[1] + 32)
    return sorted(timer_hwirqs), sorted(ufs_hwirqs), sha256(raw)


def verify_interrupt_progress(before, after, timer_hwirqs, ufs_hwirqs, runtime):
    cpu_count, rows = runtime.interrupt_deltas(before, after)
    timer_rows = [row for row in rows if row["name"] == "arch_timer"]
    if len(timer_rows) != 1 or timer_rows[0]["hwirq"] not in timer_hwirqs:
        raise ValueError("Android architected-timer IRQ does not match the saved DTB")
    observed_ufs = sorted(row["hwirq"] for row in rows if row["name"] == "ufshcd")
    if observed_ufs != ufs_hwirqs:
        raise ValueError(
            f"Android UFS IRQs differ from the saved DTB: {observed_ufs} != {ufs_hwirqs}"
        )
    timer_delta = timer_rows[0]["total_delta"]
    ufs_rows = [row for row in rows if row["name"] == "ufshcd"]
    ufs_delta = sum(row["total_delta"] for row in ufs_rows)
    if timer_delta <= 0:
        raise ValueError("architected timer did not advance during capture")
    if ufs_delta <= 0:
        raise ValueError("UFS IRQ counters did not advance during capture")
    return {
        "cpu_count": cpu_count,
        "timer": {
            "linux_irq": timer_rows[0]["linux_irq"],
            "gic_hwirq": timer_rows[0]["hwirq"],
            "total_delta": timer_delta,
            "per_cpu_delta": timer_rows[0]["per_cpu_delta"],
        },
        "ufs": {
            "expected_gic_hwirqs": ufs_hwirqs,
            "observed_gic_hwirqs": observed_ufs,
            "total_delta": ufs_delta,
            "rows": ufs_rows,
        },
    }


def collect(adb, serial, interval, runner=subprocess.run, sleeper=time.sleep):
    prefix = ("shell", "getprop")
    device = decode(
        adb_read(adb, serial, prefix + ("ro.product.device",), runner).stdout,
        "ro.product.device",
    )
    hardware = decode(
        adb_read(adb, serial, prefix + ("ro.boot.hardware",), runner).stdout,
        "ro.boot.hardware",
    )
    boot_devices = validate_boot_devices(
        decode(
            adb_read(adb, serial, prefix + ("ro.boot.boot_devices",), runner).stdout,
            "ro.boot.boot_devices",
        )
    )
    if device != "duchamp" or hardware != "mt6897":
        raise ValueError(f"unexpected target {device}/{hardware}")

    def cat(path):
        return adb_read(adb, serial, ("exec-out", "cat", path), runner).stdout

    before = cat("/proc/interrupts")
    cpuidle = cat("/sys/devices/system/cpu/cpuidle/current_driver")
    modules = cat("/proc/modules")
    scmi = adb_read(
        adb,
        serial,
        ("shell", "readlink", "-f", "/sys/bus/platform/devices/firmware:scmi/driver"),
        runner,
    ).stdout
    sleeper(interval)
    after = cat("/proc/interrupts")

    probes = {}
    for name, command in PROBES.items():
        process = adb_read(adb, serial, command, runner, required=False)
        probes[name] = probe_result(process)
    return {
        "device": device,
        "hardware": hardware,
        "boot_devices": boot_devices,
        "interrupts_before": before,
        "interrupts_after": after,
        "cpuidle": cpuidle,
        "modules": modules,
        "scmi_driver": scmi,
        "probes": probes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--reference-dtb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    if args.interval < 0.2 or args.interval > 30:
        parser.error("--interval must be between 0.2 and 30 seconds")
    if args.output.exists():
        parser.error("--output already exists")
    if not args.adb.is_file():
        parser.error("--adb does not exist")

    repo = Path(__file__).resolve().parent.parent
    runtime = load_live_parser(repo)
    devices = online_devices(args.adb)
    serial = args.serial or (devices[0] if len(devices) == 1 else None)
    if serial is None or serial not in devices:
        parser.error(f"select one online device; found {len(devices)}")
    try:
        timer_hwirqs, ufs_hwirqs, dtb_hash = expected_interrupts(
            args.reference_dtb.resolve(), repo, runtime
        )
        captured = collect(args.adb, serial, args.interval)
        progress = verify_interrupt_progress(
            decode(captured["interrupts_before"], "interrupts before"),
            decode(captured["interrupts_after"], "interrupts after"),
            timer_hwirqs,
            ufs_hwirqs,
            runtime,
        )
        cpuidle = decode(captured["cpuidle"], "cpuidle")
        scmi = decode(captured["scmi_driver"], "SCMI driver").replace("\\", "/")
        module = runtime.parse_loaded_module(
            decode(captured["modules"], "proc modules"), "ufs_mediatek_mod"
        )
        if cpuidle != "psci_idle" or not scmi.endswith("/arm-scmi"):
            raise ValueError(f"unexpected PSCI/SCMI runtime: {cpuidle}/{scmi}")
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"shell runtime check failed: {error}\n")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    raw_files = {
        "interrupts-before.txt": captured["interrupts_before"],
        "interrupts-after.txt": captured["interrupts_after"],
        "proc-modules.txt": captured["modules"],
        "cpuidle-current-driver.txt": captured["cpuidle"],
        "scmi-driver.txt": captured["scmi_driver"],
    }
    receipts = {}
    for name, raw in raw_files.items():
        (output / name).write_bytes(raw)
        receipts[name] = {"bytes": len(raw), "sha256": sha256(raw)}
    report = {
        "passed": True,
        "target": {
            "device": "duchamp",
            "hardware": "mt6897",
            "android_boot_devices": captured["boot_devices"],
            "ufs_boot_controller_matches_saved_dtb": True,
        },
        "device_serial_sha256": sha256(serial.encode()),
        "reference_dtb_sha256": dtb_hash,
        "interval_seconds": args.interval,
        "runtime": progress,
        "firmware": {
            "cpuidle_driver": cpuidle,
            "scmi_driver": scmi,
            "installed_ufs_module": module,
        },
        "access_probes": captured["probes"],
        "receipts": receipts,
        "claims": {
            "android_timer_delivery_observed": True,
            "android_ufs_irq_delivery_observed": True,
            "xnu_phone_delivery_observed": False,
            "gic_or_firmware_ownership_verified_for_xnu": False,
            "ufs_dma_or_iommu_route_verified": False,
        },
        "safety": {
            "adb_commands": ["getprop", "cat", "readlink"],
            "root_requested": False,
            "device_writes": False,
            "fastboot_access": False,
            "partition_access": False,
            "mmio_access": False,
        },
        "scope": "read-only Android shell runtime evidence; not an XNU phone or DMA test",
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
