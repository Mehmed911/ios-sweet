#!/usr/bin/env python3
"""Collect and verify read-only MT6897 runtime evidence through ADB shell.

By default only ``getprop``, ``cat`` and ``readlink`` are issued to an already
connected Android device.  An explicit ``--root-read-only`` option permits a
fixed allowlist of ``su -c`` reads for otherwise protected runtime evidence.
Neither mode writes a device file, invokes fastboot, accesses a partition or
reads MMIO.  A positive result describes Android's current GIC/timer/UFS
routing only; it does not authorize XNU MMIO or DMA.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time


EXPECTED_DTB_SHA256 = (
    "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
)
HCCAP_64_ADDRESSING_SUPPORT = 0x01000000
HCCAP_MCQ_SUPPORT = 0x40000000

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
    "ufs_dma_mask_bits": (
        "exec-out",
        "cat",
        "/sys/devices/platform/soc/112b0000.ufshci/dma_mask_bits",
    ),
    "ufs_coherent_dma_mask_bits": (
        "exec-out",
        "cat",
        "/sys/devices/platform/soc/112b0000.ufshci/coherent_dma_mask_bits",
    ),
}

ROOT_PROBES = {
    "identity": ("exec-out", "su", "-c", "id"),
    "cmdline": ("exec-out", "su", "-c", "cat /proc/cmdline"),
    "iomem": ("exec-out", "su", "-c", "cat /proc/iomem"),
    "ufs_sysfs_list": (
        "exec-out",
        "su",
        "-c",
        "ls -la /sys/devices/platform/soc/112b0000.ufshci",
    ),
    "ufs_capabilities_list": (
        "exec-out",
        "su",
        "-c",
        "ls -la /sys/devices/platform/soc/112b0000.ufshci/capabilities",
    ),
    "ufs_debugfs_list": (
        "exec-out",
        "su",
        "-c",
        "ls -la /sys/kernel/debug/ufs",
    ),
    "debugfs_root_list": (
        "exec-out",
        "su",
        "-c",
        "ls -la /sys/kernel/debug",
    ),
    "atf_log_head": (
        "exec-out",
        "su",
        "-c",
        "toybox timeout 2 head -c 262144 /proc/atf_log/atf_log",
    ),
    "ufs_iommu_group": (
        "exec-out",
        "su",
        "-c",
        "ls -ld /sys/devices/platform/soc/112b0000.ufshci/iommu_group",
    ),
    "ufs_dma_mask_bits": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/dma_mask_bits",
    ),
    "ufs_coherent_dma_mask_bits": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/coherent_dma_mask_bits",
    ),
    "ufs_recursive_list": (
        "exec-out",
        "su",
        "-c",
        "toybox timeout 3 ls -laR /sys/devices/platform/soc/112b0000.ufshci | toybox head -n 1200",
    ),
    "ufs_proc_debug": (
        "exec-out",
        "su",
        "-c",
        "toybox timeout 2 head -n 20 /proc/ufs_debug",
    ),
    "kernel_log_ufs": (
        "exec-out",
        "su",
        "-c",
        "toybox timeout 3 dmesg | toybox grep -i -E 'ufs|ufshcd|hccap|swiotlb|iommu|dma mask|dma_mask' | toybox tail -n 400",
    ),
    "ufs_scsi_can_queue": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/host0/scsi_host/host0/can_queue",
    ),
    "ufs_scsi_nr_hw_queues": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/host0/scsi_host/host0/nr_hw_queues",
    ),
    "ufs_scsi_sg_tablesize": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/host0/scsi_host/host0/sg_tablesize",
    ),
    "ufs_scsi_cmd_per_lun": (
        "exec-out",
        "su",
        "-c",
        "cat /sys/devices/platform/soc/112b0000.ufshci/host0/scsi_host/host0/cmd_per_lun",
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


def parse_dma_mask_bits(text):
    try:
        bits = int(text, 0)
    except ValueError as error:
        raise ValueError("DMA mask width is not an integer") from error
    if not 1 <= bits <= 64:
        raise ValueError("DMA mask width is outside 1..64 bits")
    return bits


def parse_bounded_nonnegative_integer(text, label, maximum=1 << 20):
    try:
        value = int(text, 0)
    except ValueError as error:
        raise ValueError(f"{label} is not an integer") from error
    if not 0 <= value <= maximum:
        raise ValueError(f"{label} is outside 0..{maximum}")
    return value


def parse_ufs_interface_inventory(text):
    """Record candidate exported names without inferring hidden registers."""
    names = set()
    for line in text.splitlines():
        fields = line.split()
        if fields and not line.endswith(":"):
            names.add(fields[-1])
    hccap_names = sorted(
        name for name in names
        if re.fullmatch(r"(?i)(hccap|hci_cap|host_capabilities|controller_capabilities)", name)
    )
    dma_mask_names = sorted(
        name for name in names
        if re.fullmatch(r"(?i)(dma_mask_bits|coherent_dma_mask_bits)", name)
    )
    return {
        "status": "captured",
        "bounded_lines": len(text.splitlines()),
        "hccap_candidate_entries": hccap_names,
        "dma_mask_candidate_entries": dma_mask_names,
    }


def parse_ufs_proc_debug(text):
    """Parse the bounded, read-only MTK UFS proc summary.

    ``Host capabilities`` is the live driver's effective ``hba->capabilities``
    value.  It is not treated as proof of an accepted DMA mask or ownership.
    """

    def one(pattern, label):
        matches = re.findall(pattern, text, re.MULTILINE)
        if len(matches) != 1:
            raise ValueError(f"UFS proc debug lacks one unambiguous {label}")
        return matches[0]

    capability_fields = one(
        r"^Host capabilities=(0x[0-9a-fA-F]+), "
        r"hba-caps=(0x[0-9a-fA-F]+), mtk-caps:(0x[0-9a-fA-F]+)$",
        "capability line",
    )
    version_fields = one(
        r"^ver\. host=(0x[0-9a-fA-F]+), dev=(0x[0-9a-fA-F]+)$",
        "version line",
    )
    mcq_fields = one(
        r"^MCQ sup\./en\.: ([01])/([01]), nr_hw_queues=([0-9]+)$",
        "MCQ line",
    )
    queue_fields = one(
        r"^nutrs=([0-9]+), dev_info\.bqueuedepth=([0-9]+)$",
        "queue-depth line",
    )

    capabilities, hba_caps, mtk_caps = (
        int(field, 16) for field in capability_fields
    )
    host_version, device_version = (int(field, 16) for field in version_fields)
    mcq_supported, mcq_enabled, nr_hw_queues = (
        int(field, 10) for field in mcq_fields
    )
    nutrs, device_queue_depth = (int(field, 10) for field in queue_fields)
    for label, value in (
        ("host capabilities", capabilities),
        ("hba caps", hba_caps),
        ("MTK caps", mtk_caps),
        ("host version", host_version),
        ("device version", device_version),
    ):
        if not 0 <= value <= 0xFFFFFFFF:
            raise ValueError(f"UFS proc debug {label} is outside 32 bits")
    for label, value in (
        ("nr_hw_queues", nr_hw_queues),
        ("nutrs", nutrs),
        ("device queue depth", device_queue_depth),
    ):
        if not 1 <= value <= 1 << 16:
            raise ValueError(f"UFS proc debug {label} is outside 1..65536")

    hccap_mcq = bool(capabilities & HCCAP_MCQ_SUPPORT)
    if bool(mcq_supported) != hccap_mcq:
        raise ValueError("UFS proc debug MCQ support conflicts with HCCAP")
    if mcq_enabled and (not mcq_supported or nr_hw_queues <= 1):
        raise ValueError("UFS proc debug MCQ enabled state is inconsistent")
    return {
        "status": "observed",
        "source": "/proc/ufs_debug",
        "effective_host_capabilities": f"0x{capabilities:08x}",
        "hba_caps": f"0x{hba_caps:08x}",
        "mtk_caps": f"0x{mtk_caps:08x}",
        "host_version": f"0x{host_version:03x}",
        "device_version": f"0x{device_version:03x}",
        "supports_64_bit_addressing": bool(
            capabilities & HCCAP_64_ADDRESSING_SUPPORT
        ),
        "mcq_supported": bool(mcq_supported),
        "mcq_enabled": bool(mcq_enabled),
        "nr_hw_queues": nr_hw_queues,
        "nutrs": nutrs,
        "device_queue_depth": device_queue_depth,
        "effective_dma_mask_bits": None,
    }


def kernel_cmdline_value(text, key):
    values = [
        token.split("=", 1)[1]
        for token in text.split()
        if token.startswith(key + "=")
    ]
    if len(values) != 1 or not values[0]:
        raise ValueError(f"kernel command line lacks one unambiguous {key}= value")
    return values[0]


def kernel_cmdline_observation(process, key="swiotlb"):
    """Describe a read-only cmdline probe without promoting missing access."""
    probe = probe_result(process)
    if not probe["readable"]:
        return {"status": probe["status"], "value": None}
    text = decode(process.stdout, "kernel command line")
    values = [
        token.split("=", 1)[1]
        for token in text.split()
        if token.startswith(key + "=")
    ]
    if not values:
        return {"status": "not-specified", "value": None}
    if len(values) != 1 or not values[0]:
        raise ValueError(
            f"kernel command line lacks one unambiguous {key}= value"
        )
    return {"status": "specified", "value": values[0]}


def parse_atf_identity(text):
    """Parse identity strings only; do not infer service effects or ownership."""

    def marker(pattern):
        match = re.search(pattern, text, re.MULTILINE)
        return match.group(1).strip() if match else None

    release = marker(r"^.*BL31:\s+(?!Built\s*:)([^\r\n]+)$")
    built = marker(r"^.*BL31:\s+Built\s*:\s*([^\r\n]+)$")
    if release is None and built is None:
        return {
            "status": "not-found-in-bounded-capture",
            "release": None,
            "built": None,
            "software_version": None,
            "software_build_time": None,
        }
    if release is None or built is None:
        raise ValueError("bounded ATF log contains a partial BL31 identity")
    return {
        "status": "observed",
        "release": release,
        "built": built,
        "software_version": marker(r"^.*Software version:\s*([^\r\n]+)$"),
        "software_build_time": marker(r"^.*Build time:\s*([^\r\n]+)$"),
    }


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


def adb_root_read(adb, serial, command, runner=subprocess.run):
    if command not in ROOT_PROBES.values():
        raise ValueError(f"refusing non-allowlisted root read: {command}")
    return run_command([str(adb), "-s", serial, *command], runner)


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


def collect(
    adb,
    serial,
    interval,
    root_read_only=False,
    runner=subprocess.run,
    sleeper=time.sleep,
):
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
    cmdline = adb_read(
        adb,
        serial,
        ("exec-out", "cat", "/proc/cmdline"),
        runner,
        required=False,
    )
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
        result = probe_result(process)
        if name in ("ufs_dma_mask_bits", "ufs_coherent_dma_mask_bits"):
            result["value"] = (
                parse_dma_mask_bits(decode(process.stdout, name))
                if result["readable"]
                else None
            )
        probes[name] = result

    root_probes = {}
    if root_read_only:
        for name, command in ROOT_PROBES.items():
            process = adb_root_read(adb, serial, command, runner)
            result = probe_result(process)
            if name in ("ufs_dma_mask_bits", "ufs_coherent_dma_mask_bits"):
                result["value"] = (
                    parse_dma_mask_bits(decode(process.stdout, name))
                    if result["readable"]
                    else None
                )
            elif name.startswith("ufs_scsi_"):
                result["value"] = (
                    parse_bounded_nonnegative_integer(
                        decode(process.stdout, name), name
                    )
                    if result["readable"]
                    else None
                )
            root_probes[name] = {"process": process, "result": result}
        identity = root_probes["identity"]
        if not identity["result"]["readable"] or not decode(
            identity["process"].stdout, "root identity"
        ).startswith("uid=0("):
            raise ValueError("root read-only mode did not obtain uid 0")
    return {
        "device": device,
        "hardware": hardware,
        "boot_devices": boot_devices,
        "interrupts_before": before,
        "interrupts_after": after,
        "cpuidle": cpuidle,
        "modules": modules,
        "cmdline": cmdline,
        "scmi_driver": scmi,
        "probes": probes,
        "root_probes": root_probes,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--reference-dtb", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument(
        "--root-read-only",
        action="store_true",
        help="run only the fixed root read allowlist; never write the device",
    )
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
        captured = collect(
            args.adb, serial, args.interval, root_read_only=args.root_read_only
        )
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
        root_probes = captured["root_probes"]
        cmdline_process = (
            root_probes["cmdline"]["process"]
            if root_probes
            and root_probes["cmdline"]["result"]["readable"]
            else captured["cmdline"]
        )
        swiotlb_policy = kernel_cmdline_observation(cmdline_process)
        if root_probes:
            capability_probe = root_probes["ufs_capabilities_list"]
            debugfs_probe = root_probes["ufs_debugfs_list"]
            hccap = runtime.hccap_exposure(
                decode(capability_probe["process"].stdout, "UFS capabilities")
                if capability_probe["result"]["readable"]
                else "",
                decode(debugfs_probe["process"].stdout, "UFS debugfs")
                if debugfs_probe["result"]["readable"]
                else "",
            )
            hccap["source_status"] = {
                "sysfs_capabilities": capability_probe["result"]["status"],
                "debugfs": debugfs_probe["result"]["status"],
            }
            inventory_probe = root_probes["ufs_recursive_list"]
            interface_inventory = (
                parse_ufs_interface_inventory(
                    decode(inventory_probe["process"].stdout,
                           "bounded UFS interface inventory")
                )
                if inventory_probe["result"]["readable"]
                else {
                    "status": inventory_probe["result"]["status"],
                    "bounded_lines": 0,
                    "hccap_candidate_entries": [],
                    "dma_mask_candidate_entries": [],
                }
            )
            hccap["recursive_interface_inventory"] = interface_inventory
            proc_debug_probe = root_probes["ufs_proc_debug"]
            proc_debug = (
                parse_ufs_proc_debug(
                    decode(proc_debug_probe["process"].stdout,
                           "bounded UFS proc debug")
                )
                if proc_debug_probe["result"]["readable"]
                else {
                    "status": proc_debug_probe["result"]["status"],
                    "source": "/proc/ufs_debug",
                    "effective_host_capabilities": None,
                    "effective_dma_mask_bits": None,
                }
            )
            hccap["proc_debug"] = proc_debug
            if proc_debug["status"] == "observed":
                hccap["status"] = "observed-via-proc-debug"
                hccap["value"] = proc_debug["effective_host_capabilities"]
                hccap["supports_64_bit_addressing"] = proc_debug[
                    "supports_64_bit_addressing"
                ]
            scsi_queue = {
                key.removeprefix("ufs_scsi_"): root_probes[key]["result"]
                for key in (
                    "ufs_scsi_can_queue",
                    "ufs_scsi_nr_hw_queues",
                    "ufs_scsi_sg_tablesize",
                    "ufs_scsi_cmd_per_lun",
                )
            }
            bounded_kernel_log = root_probes["kernel_log_ufs"]["result"]
            atf_probe = root_probes["atf_log_head"]
            atf_identity = (
                parse_atf_identity(
                    decode(atf_probe["process"].stdout, "bounded ATF log")
                )
                if atf_probe["result"]["readable"]
                else {
                    "status": atf_probe["result"]["status"],
                    "release": None,
                    "built": None,
                    "software_version": None,
                    "software_build_time": None,
                }
            )
        else:
            hccap = {"status": "not-captured", "value": None}
            scsi_queue = {
                "status": "not-captured",
            }
            bounded_kernel_log = {"status": "not-captured"}
            atf_identity = {
                "status": "not-captured",
                "release": None,
                "built": None,
                "software_version": None,
                "software_build_time": None,
            }
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
        "cmdline.stdout.txt": captured["cmdline"].stdout,
        "cmdline.stderr.txt": captured["cmdline"].stderr,
        "cmdline.exit.txt": str(captured["cmdline"].returncode).encode("ascii"),
    }
    for name, item in captured["root_probes"].items():
        process = item["process"]
        raw_files[f"root-{name}.stdout.txt"] = process.stdout
        raw_files[f"root-{name}.stderr.txt"] = process.stderr
        raw_files[f"root-{name}.exit.txt"] = str(process.returncode).encode(
            "ascii"
        )
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
            "installed_bl31_identity": atf_identity,
        },
        "access_probes": captured["probes"],
        "root_access_probes": {
            name: item["result"] for name, item in captured["root_probes"].items()
        },
        "runtime_ufs_contract": {
            "hccap": hccap,
            "streaming_dma_mask_bits": (
                captured["root_probes"]["ufs_dma_mask_bits"]["result"]
                if captured["root_probes"]
                else captured["probes"]["ufs_dma_mask_bits"]
            ),
            "coherent_dma_mask_bits": (
                captured["root_probes"]["ufs_coherent_dma_mask_bits"]["result"]
                if captured["root_probes"]
                else captured["probes"]["ufs_coherent_dma_mask_bits"]
            ),
            "dma_ops": {"status": "not-captured", "value": None},
            "iommu_fwspec": {"status": "not-captured", "value": None},
            "iommu_domain": {"status": "not-captured", "value": None},
            "swiotlb_pool": {
                "status": "not-captured",
                "value": None,
                "cmdline_policy": swiotlb_policy,
            },
            "cache_ownership": {"status": "unverified", "value": None},
            "scsi_host_queue": scsi_queue,
            "bounded_kernel_log_ufs": bounded_kernel_log,
        },
        "receipts": receipts,
        "claims": {
            "android_timer_delivery_observed": True,
            "android_ufs_irq_delivery_observed": True,
            "android_ufs_multiqueue_observed": (
                bool(root_probes)
                and scsi_queue["nr_hw_queues"].get("value", 0) > 1
            ),
            "android_ufs_hccap_observed": (
                hccap.get("status") == "observed-via-proc-debug"
            ),
            "xnu_phone_delivery_observed": False,
            "gic_or_firmware_ownership_verified_for_xnu": False,
            "installed_bl31_identity_observed": (
                atf_identity["status"] == "observed"
            ),
            "installed_bl31_ufs_effect_contract_verified": False,
            "ufs_dma_or_iommu_route_verified": False,
        },
        "safety": {
            "adb_commands": ["getprop", "cat", "readlink"]
            + (["su", "id", "ls", "toybox", "timeout", "head", "dmesg", "grep", "tail"] if args.root_read_only else []),
            "root_requested": args.root_read_only,
            "root_commands_allowlisted": args.root_read_only,
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
