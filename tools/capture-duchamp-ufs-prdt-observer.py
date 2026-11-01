#!/usr/bin/env python3
"""Run one separately approved, bounded Duchamp UFS PRDT observation.

This command changes the running Android kernel by temporarily loading an
exact, statically verified module.  It never flashes or accesses a partition,
changes SELinux, drops caches, invokes firmware, or performs MMIO.  Its fixed
workload only reads regular system files into /dev/null.  Cleanup is attempted
on every exit and a reboot is never issued automatically.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


APPROVAL_PREFIX = "I_APPROVE_DUCHAMP_PRDT_"
EXPECTED_DEVICE = "duchamp"
EXPECTED_HARDWARE = "mt6897"
EXPECTED_KERNEL = "6.1.57-android14-11-gcf2c2dc91b9e-ab11782407"
EXPECTED_GKI_COMMIT = "cf2c2dc91b9e9f016dc25cf095b1fe34cb5dfcb6"
EXPECTED_VERMAGIC = (
    "6.1.57-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64"
)
EXPECTED_BUS_DMA_LIMIT = 0x0000000FFFFFFFFF
MODULE_NAME = "duchamp_ufs_prdt_observer"
SYSFS_ATTRIBUTE = (
    "/sys/devices/platform/soc/112b0000.ufshci/"
    "sweet_ufs_prdt_observation"
)
ORPHAN_TRACE_INSTANCE = "/sys/kernel/tracing/instances/sweet_ufs_probe_v1"
EXPECTED_UFS_BUILD_ID_NOTE = bytes.fromhex(
    "040000001400000003000000474e5500"
    "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
)
READ_FILES = (
    "/system/apex/com.android.btservices.apex",
    "/system/apex/com.android.i18n.apex",
    "/system/apex/com.android.vndk.current.apex",
    "/system/apex/com.google.android.art.apex",
    "/system/apex/com.google.android.media.swcodec.apex",
    "/system/framework/arm64/boot-framework.oat",
    "/system/framework/framework.jar",
    "/system/framework/services.jar",
)

DECIMAL_FIELDS = {
    "observation_version",
    "root_read_only",
    "coherent_snapshot",
    "runtime_direct_dma_contract",
    "hook_calls",
    "target_calls",
    "rejected_calls",
    "commands",
    "segments",
    "read_commands",
    "write_commands",
    "bidirectional_commands",
    "unknown_direction_commands",
    "hook_error_calls",
    "zero_length_segments",
    "dma_end_overflows",
    "translated_phys_invalid",
    "original_phys_end_overflows",
    "prdt_address_mismatches",
    "prdt_length_mismatches",
    "swiotlb_segments",
    "dma_to_phys_matches",
    "dma_to_phys_mismatches",
    "above_4g_segments",
    "outside_bus_limit_segments",
    "runtime_contract_changes",
    "max_segment_length",
    "all_prdt_entries_match",
    "observation_complete",
    "all_segments_within_bus_limit",
    "all_dma_equals_original_without_swiotlb",
}
HEX_FIELDS = {
    "min_dma_address",
    "max_dma_end",
    "min_translated_phys",
    "max_translated_phys_end",
    "min_original_phys",
    "max_original_phys_end",
    "runtime_bus_dma_limit",
}
COUNTER_FIELDS = DECIMAL_FIELDS - {
    "observation_version",
    "root_read_only",
    "coherent_snapshot",
    "runtime_direct_dma_contract",
    "all_prdt_entries_match",
    "observation_complete",
    "all_segments_within_bus_limit",
    "all_dma_equals_original_without_swiotlb",
}
ZERO_REQUIRED_FIELDS = {
    "rejected_calls",
    "hook_error_calls",
    "unknown_direction_commands",
    "zero_length_segments",
    "dma_end_overflows",
    "translated_phys_invalid",
    "original_phys_end_overflows",
    "prdt_address_mismatches",
    "prdt_length_mismatches",
    "outside_bus_limit_segments",
    "runtime_contract_changes",
}
KERNEL_FAULT = re.compile(
    (
        r"(?:Kernel panic|Unable to handle kernel|Internal error:|Oops:|BUG:|"
        r"Call trace:|WARNING:|SError|RCU[^\n]*stall|hung task|soft lockup|"
        r"hard LOCKUP|KASAN|use-after-free)"
    ),
    re.IGNORECASE,
)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    return sha256_bytes(path.read_bytes())


def decode(raw, label):
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeError as error:
        raise ValueError(f"{label} is not UTF-8") from error


def run(argv, timeout=30):
    return subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def require_success(result, label):
    if result.returncode:
        stderr = decode(result.stderr, label + " stderr")
        raise RuntimeError(f"{label} failed ({result.returncode}): {stderr}")
    return decode(result.stdout, label + " stdout")


def parse_devices(text):
    devices = []
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "device":
            devices.append(fields[0])
    return devices


def parse_observation(text):
    values = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        if line.count("=") != 1:
            raise ValueError("malformed PRDT observation line")
        key, raw = line.split("=", 1)
        if key in values:
            raise ValueError("duplicate PRDT observation field: " + key)
        if key in DECIMAL_FIELDS:
            if not raw.isdecimal():
                raise ValueError("invalid decimal PRDT field: " + key)
            values[key] = int(raw, 10)
        elif key in HEX_FIELDS:
            if not re.fullmatch(r"0x[0-9a-fA-F]{16}", raw):
                raise ValueError("invalid hexadecimal PRDT field: " + key)
            values[key] = int(raw, 16)
        else:
            raise ValueError("unexpected PRDT observation field: " + key)

    missing = sorted((DECIMAL_FIELDS | HEX_FIELDS) - set(values))
    if missing:
        raise ValueError("missing PRDT observation fields: " + ", ".join(missing))
    if values["observation_version"] != 2 or values["root_read_only"] != 1:
        raise ValueError("unexpected PRDT observation contract")
    for field in (
        "coherent_snapshot",
        "runtime_direct_dma_contract",
        "observation_complete",
        "all_prdt_entries_match",
        "all_segments_within_bus_limit",
        "all_dma_equals_original_without_swiotlb",
    ):
        if values[field] not in (0, 1):
            raise ValueError("invalid PRDT observation flag: " + field)
    if values["runtime_bus_dma_limit"] != EXPECTED_BUS_DMA_LIMIT:
        raise ValueError("runtime UFS bus DMA limit changed")
    if values["hook_calls"] < values["target_calls"]:
        raise ValueError("target calls exceed all hook calls")
    if values["target_calls"] != (
        values["commands"] + values["rejected_calls"]
    ):
        raise ValueError("target-call accounting is inconsistent")
    directions = sum(
        values[field]
        for field in (
            "read_commands",
            "write_commands",
            "bidirectional_commands",
            "unknown_direction_commands",
        )
    )
    if directions != values["commands"]:
        raise ValueError("command direction accounting is inconsistent")
    if values["swiotlb_segments"] > values["segments"]:
        raise ValueError("SWIOTLB segments exceed observed segments")
    if values["above_4g_segments"] > values["segments"]:
        raise ValueError("above-4G segments exceed observed segments")
    return values


def evaluate_observations(before, after):
    delta = {}
    for field in sorted(COUNTER_FIELDS):
        if after[field] < before[field]:
            raise ValueError("PRDT counter moved backwards: " + field)
        delta[field] = after[field] - before[field]

    errors = []
    if delta["commands"] <= 0:
        errors.append("no new UFS command reached the observer")
    if delta["segments"] <= 0:
        errors.append("no new UFS DMA segment reached the observer")
    if delta["read_commands"] <= 0:
        errors.append("the bounded observation window contained no read command")
    for field in sorted(ZERO_REQUIRED_FIELDS):
        if after[field] != 0:
            errors.append(f"{field} is non-zero")
    if after["segments"] != (
        after["dma_to_phys_matches"] + after["dma_to_phys_mismatches"]
    ):
        errors.append("DMA-to-physical segment accounting is incomplete")
    if after["all_prdt_entries_match"] != 1:
        errors.append("PRDT entries do not all match mapped scatterlist entries")
    if after["coherent_snapshot"] != 1:
        errors.append("the kernel report is not a coherent snapshot")
    if after["runtime_direct_dma_contract"] != 1:
        errors.append("the pinned dma-direct/no-IOMMU contract changed")
    if after["observation_complete"] != 1:
        errors.append("the kernel marked the observation incomplete")
    if after["all_segments_within_bus_limit"] != 1:
        errors.append("a complete DMA extent exceeds the live bus DMA limit")
    if after["segments"]:
        for low, high in (
            ("min_dma_address", "max_dma_end"),
            ("min_translated_phys", "max_translated_phys_end"),
            ("min_original_phys", "max_original_phys_end"),
        ):
            if after[low] > after[high]:
                errors.append(f"invalid observed extent: {low}/{high}")

    if (
        after["dma_to_phys_matches"] == after["segments"]
        and after["swiotlb_segments"] == 0
    ):
        route = "dma-equals-original-phys-no-swiotlb-under-pinned-contract"
    elif after["swiotlb_segments"] > 0:
        route = "swiotlb-buffer-observed-under-pinned-contract"
    else:
        route = "dma-differs-from-original-phys-without-swiotlb-observed"
    expected_equal_flag = int(
        after["observation_complete"] == 1
        and after["dma_to_phys_matches"] == after["segments"]
        and after["swiotlb_segments"] == 0
        and after["translated_phys_invalid"] == 0
    )
    if after["all_dma_equals_original_without_swiotlb"] != expected_equal_flag:
        errors.append("DMA/physical equality summary flag is inconsistent")

    return {
        "passed": not errors,
        "errors": errors,
        "delta": delta,
        "route_classification": route,
        "read_workload_causality_proven": False,
        "linux_dma_direct_contract_pinned_during_snapshots": True,
        "physical_firewall_bypass_proven": False,
        "xnu_cache_ownership_proven": False,
    }


def appended_kernel_lines(before, after):
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    if not before_lines:
        return after_lines, True
    limit = min(len(before_lines), len(after_lines))
    for overlap in range(limit, 0, -1):
        if before_lines[-overlap:] == after_lines[:overlap]:
            return after_lines[overlap:], True
    return after_lines, False


def validate_static_verification(module_path, source_path, verification_path):
    report = json.loads(verification_path.read_text(encoding="utf-8"))
    if report.get("verdict") != "static-verification-passed":
        raise ValueError("module static verification did not pass")
    if report.get("target") != {"device": "duchamp", "soc": "mt6897"}:
        raise ValueError("module static-verification target differs")
    build = report.get("build", {})
    if build.get("gki_commit") != EXPECTED_GKI_COMMIT:
        raise ValueError("module GKI source commit differs")
    if build.get("vermagic") != EXPECTED_VERMAGIC:
        raise ValueError("module vermagic differs")
    module = report.get("module", {})
    if module.get("name") != module_path.name:
        raise ValueError("verified module name differs")
    if module.get("sha256") != sha256_file(module_path):
        raise ValueError("verified module hash differs")
    if module.get("bytes") != module_path.stat().st_size:
        raise ValueError("verified module size differs")
    if module.get("this_module_bytes") != 1088:
        raise ValueError("verified struct module size differs")
    if module.get("this_module_relocation_offsets") != [368, 984]:
        raise ValueError("verified module init/exit offsets differ")
    if module.get("signature_appended") is not False:
        raise ValueError("unexpected module signature state")
    source = report.get("source", {})
    if source.get("sha256") != sha256_file(source_path):
        raise ValueError("verified source hash differs")
    safety = report.get("safety", {})
    if safety.get("module_loaded") is not False:
        raise ValueError("static-verification receipt is not offline-only")
    return report


class AdbTarget:
    def __init__(self, adb, serial):
        self.prefix = [str(adb), "-s", serial]

    def command(self, *args, timeout=30):
        return run(self.prefix + list(args), timeout=timeout)

    def shell(self, *args, timeout=30):
        return self.command("shell", *args, timeout=timeout)

    def root(self, command, timeout=30):
        return self.shell("su", "-c", command, timeout=timeout)


def root_text(target, command, label, timeout=30):
    return require_success(target.root(command, timeout=timeout), label)


def shell_text(target, args, label, timeout=30):
    return require_success(target.shell(*args, timeout=timeout), label)


def root_bytes(target, command, label, timeout=30):
    result = target.root(command, timeout=timeout)
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{label} failed ({result.returncode}): {stderr}")
    return result.stdout


def kernel_log_tail(target):
    text = root_text(target, "dmesg", "kernel log", timeout=30)
    if not text:
        raise RuntimeError("kernel log is unexpectedly empty")
    return "\n".join(text.splitlines()[-400:])


def approval_token(module_hash):
    return APPROVAL_PREFIX + module_hash.upper()


def battery_level(text):
    match = re.search(r"^\s*level:\s*(\d+)\s*$", text, re.MULTILINE)
    if not match:
        raise ValueError("cannot read battery level")
    level = int(match.group(1))
    if not 0 <= level <= 100:
        raise ValueError("invalid battery level")
    return level


def write_text(path, text):
    path.write_text(text + ("\n" if text and not text.endswith("\n") else ""),
                    encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--serial")
    parser.add_argument("--approval-token", required=True)
    args = parser.parse_args()

    for path, label in (
        (args.adb, "ADB"),
        (args.module, "module"),
        (args.source, "source"),
        (args.verification, "verification receipt"),
    ):
        if not path.is_file():
            parser.error(f"{label} does not exist")
    if args.output.exists():
        parser.error("preserve existing output")

    verification = validate_static_verification(
        args.module, args.source, args.verification
    )
    module_hash = verification["module"]["sha256"]
    if args.approval_token != approval_token(module_hash):
        parser.error("approval token does not name the exact verified module hash")
    devices_result = run([str(args.adb), "devices"])
    devices = parse_devices(require_success(devices_result, "adb devices"))
    serial = args.serial or (devices[0] if len(devices) == 1 else None)
    if serial is None or serial not in devices:
        parser.error(f"select one online device; found {len(devices)}")

    target = AdbTarget(args.adb, serial)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    remote_module = f"/data/local/tmp/{MODULE_NAME}-{module_hash[:16]}.ko"
    report = {
        "report_version": 1,
        "passed": False,
        "target": {},
        "artifact": {
            "name": args.module.name,
            "bytes": args.module.stat().st_size,
            "sha256": module_hash,
            "static_verification": "passed",
        },
        "preflight": {},
        "execution": {
            "module_loaded": False,
            "module_unloaded": False,
            "staged_file_removed": False,
            "cleanup_clean": False,
        },
        "workload": [],
        "observation": None,
        "errors": [],
        "safety": {
            "fresh_explicit_approval_required": True,
            "approval_bound_to_module_sha256": module_hash,
            "temporary_live_kernel_change": True,
            "temporary_phone_file_staging": True,
            "fixed_regular_files_read_to_dev_null": True,
            "partition_access": False,
            "boot_partition_modified": False,
            "selinux_policy_changed": False,
            "tracefs_control_changed": False,
            "cache_drop_requested": False,
            "reboot_requested": False,
            "mmio_access_issued_by_observer": False,
            "firmware_call_issued_by_observer": False,
            "dma_mapping_issued_by_observer": False,
            "storage_command_issued_by_observer": False,
        },
    }
    loaded = False
    staged = False
    stage_attempted = False
    load_attempted = False
    boot_id_before = None
    taint_before = None
    dmesg_before = ""

    try:
        device = shell_text(target, ("getprop", "ro.product.device"), "device")
        hardware = shell_text(target, ("getprop", "ro.boot.hardware"), "hardware")
        kernel = shell_text(target, ("uname", "-r"), "kernel release")
        if (device, hardware, kernel) != (
            EXPECTED_DEVICE,
            EXPECTED_HARDWARE,
            EXPECTED_KERNEL,
        ):
            raise RuntimeError(f"unexpected target {device}/{hardware}/{kernel}")
        report["target"] = {
            "device": device,
            "hardware": hardware,
            "kernel": kernel,
            "serial_sha256": sha256_bytes(serial.encode("utf-8")),
        }

        identity = root_text(target, "id", "root identity")
        if not identity.startswith("uid=0(root)"):
            raise RuntimeError("root identity is unavailable")
        boot_completed = shell_text(
            target, ("getprop", "sys.boot_completed"), "boot completion"
        )
        if boot_completed != "1":
            raise RuntimeError("Android boot is incomplete")
        level = battery_level(
            shell_text(target, ("dumpsys", "battery"), "battery state")
        )
        if level < 30:
            raise RuntimeError("battery level is below the 30% safety floor")
        modules_disabled = root_text(
            target, "cat /proc/sys/kernel/modules_disabled", "module policy"
        )
        if modules_disabled != "0":
            raise RuntimeError("kernel module loading is disabled")
        if target.root(f"test ! -d {ORPHAN_TRACE_INSTANCE}").returncode:
            raise RuntimeError(
                "orphan tracefs instance remains; perform a separately approved "
                "normal Android reboot before loading another observer"
            )
        if target.root(f"test ! -d /sys/module/{MODULE_NAME}").returncode:
            raise RuntimeError("observer module is already loaded")
        if target.root(f"test ! -e {SYSFS_ATTRIBUTE}").returncode:
            raise RuntimeError("observer sysfs attribute already exists")
        if target.root(f"test ! -e {remote_module}").returncode:
            raise RuntimeError("remote staging path already exists")
        if target.root("grep -q '^ufs_mediatek_mod ' /proc/modules").returncode:
            raise RuntimeError("the pinned MediaTek UFS module is not live")
        ufs_note = root_bytes(
            target,
            "cat /sys/module/ufs_mediatek_mod/notes/.note.gnu.build-id",
            "installed UFS module build ID",
        )
        if ufs_note != EXPECTED_UFS_BUILD_ID_NOTE:
            raise RuntimeError("installed MediaTek UFS module build ID differs")

        boot_id_before = root_text(
            target, "cat /proc/sys/kernel/random/boot_id", "boot id"
        )
        taint_before = int(root_text(target, "cat /proc/sys/kernel/tainted",
                                     "kernel taint"))
        dmesg_before = kernel_log_tail(target)
        write_text(output / "dmesg-before.txt", dmesg_before)
        report["preflight"] = {
            "root": True,
            "boot_completed": True,
            "battery_level": level,
            "modules_disabled": 0,
            "orphan_tracefs_instance_absent": True,
            "observer_absent": True,
            "installed_ufs_module_live": True,
            "installed_ufs_module_build_id": (
                "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
            ),
            "kernel_taint": taint_before,
            "boot_id_sha256": sha256_bytes(boot_id_before.encode("utf-8")),
        }

        stage_attempted = True
        push = target.command("push", str(args.module), remote_module, timeout=60)
        require_success(push, "module staging")
        staged = True
        root_text(target, f"chmod 0400 {remote_module}", "staging permissions")
        remote_hash = root_text(
            target, f"toybox sha256sum {remote_module}", "remote module hash"
        ).split()[0]
        if remote_hash != module_hash:
            raise RuntimeError("staged module hash differs")

        load_attempted = True
        insmod = target.root(f"insmod {remote_module}", timeout=30)
        require_success(insmod, "observer module load")
        loaded = True
        report["execution"]["module_loaded"] = True
        if target.root(f"test -d /sys/module/{MODULE_NAME}").returncode:
            raise RuntimeError("observer module did not appear in sysfs")
        if target.root(f"test -r {SYSFS_ATTRIBUTE}").returncode:
            raise RuntimeError("observer report is not root-readable")
        mode = root_text(
            target, f"toybox stat -c %a {SYSFS_ATTRIBUTE}", "observer mode"
        )
        if mode != "400":
            raise RuntimeError("observer report mode is not 0400")

        before_text = root_text(
            target, f"cat {SYSFS_ATTRIBUTE}", "initial PRDT observation"
        )
        before = parse_observation(before_text)
        write_text(output / "observation-before.txt", before_text)

        for path in READ_FILES:
            started = time.monotonic()
            read_result = target.shell(
                "toybox",
                "timeout",
                "45",
                "toybox",
                "dd",
                f"if={path}",
                "of=/dev/null",
                "bs=1048576",
                "status=none",
                timeout=65,
            )
            row = {
                "path": path,
                "exit": read_result.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "stderr": decode(read_result.stderr, "read workload stderr"),
            }
            report["workload"].append(row)
            if read_result.returncode:
                raise RuntimeError("fixed read workload failed: " + path)

        after_text = root_text(
            target, f"cat {SYSFS_ATTRIBUTE}", "final PRDT observation"
        )
        after = parse_observation(after_text)
        write_text(output / "observation-after.txt", after_text)
        report["observation"] = evaluate_observations(before, after)
        report["observation"]["before"] = before
        report["observation"]["after"] = after
        if not report["observation"]["passed"]:
            raise RuntimeError("PRDT observation did not satisfy its invariants")

    except Exception as error:  # cleanup and preserve evidence on every failure
        report["errors"].append(str(error))
    finally:
        online = False
        try:
            online_result = run([str(args.adb), "devices"])
            online = serial in parse_devices(require_success(
                online_result, "adb devices during cleanup"
            ))
        except Exception as error:
            report["errors"].append("cleanup device check: " + str(error))

        if online:
            def cleanup_root(command, label, timeout=30):
                try:
                    return target.root(command, timeout=timeout)
                except Exception as error:
                    report["errors"].append(f"{label}: {error}")
                    return None

            if load_attempted:
                present_result = cleanup_root(
                    f"test -d /sys/module/{MODULE_NAME}",
                    "module-presence cleanup check",
                )
                present = bool(
                    present_result is not None and present_result.returncode == 0
                )
                if loaded or present:
                    unload = cleanup_root(
                        f"rmmod {MODULE_NAME}", "module unload", timeout=30
                    )
                    if unload is not None and unload.returncode:
                        report["errors"].append(
                            "module unload failed: "
                            + unload.stderr.decode(
                                "utf-8", errors="replace"
                            ).strip()
                        )
                    elif unload is not None:
                        loaded = False

            if stage_attempted:
                remove = cleanup_root(
                    f"rm -f {remote_module}", "staged-file cleanup"
                )
                if remove is not None and remove.returncode:
                    report["errors"].append(
                        "staged-file cleanup failed: "
                        + remove.stderr.decode("utf-8", errors="replace").strip()
                    )
                elif remove is not None:
                    staged = False

            module_check = cleanup_root(
                f"test ! -d /sys/module/{MODULE_NAME}",
                "final module-absence check",
            )
            attribute_check = cleanup_root(
                f"test ! -e {SYSFS_ATTRIBUTE}",
                "final attribute-absence check",
            )
            file_check = cleanup_root(
                f"test ! -e {remote_module}",
                "final staged-file-absence check",
            )
            module_absent = bool(
                module_check is not None and module_check.returncode == 0
            )
            attribute_absent = bool(
                attribute_check is not None and attribute_check.returncode == 0
            )
            file_absent = bool(file_check is not None and file_check.returncode == 0)
            report["execution"]["module_unloaded"] = bool(
                load_attempted and module_absent
            )
            report["execution"]["staged_file_removed"] = bool(
                stage_attempted and file_absent
            )
            try:
                boot_id_after = root_text(
                    target, "cat /proc/sys/kernel/random/boot_id", "final boot id"
                )
                taint_after = int(root_text(
                    target, "cat /proc/sys/kernel/tainted", "final kernel taint"
                ))
                dmesg_after = kernel_log_tail(target)
                write_text(output / "dmesg-after.txt", dmesg_after)
                new_lines, comparable = appended_kernel_lines(
                    dmesg_before, dmesg_after
                )
                faults = [line for line in new_lines if KERNEL_FAULT.search(line)]
                report["execution"].update({
                    "boot_id_unchanged": boot_id_before == boot_id_after,
                    "kernel_taint_before": taint_before,
                    "kernel_taint_after": taint_after,
                    "kernel_taint_unchanged": taint_before == taint_after,
                    "kernel_log_comparable": comparable,
                    "new_kernel_fault_lines": faults,
                })
                report["execution"]["cleanup_clean"] = all((
                    load_attempted,
                    stage_attempted,
                    module_absent,
                    attribute_absent,
                    file_absent,
                    boot_id_before == boot_id_after,
                    taint_before == taint_after,
                    comparable,
                    not faults,
                ))
            except Exception as error:
                report["errors"].append("cleanup verification: " + str(error))
        else:
            report["errors"].append(
                "device offline during cleanup; no reboot was attempted"
            )

        observation_passed = bool(
            report["observation"] and report["observation"].get("passed")
        )
        report["passed"] = bool(
            observation_passed
            and report["execution"]["module_loaded"]
            and report["execution"]["module_unloaded"]
            and report["execution"]["cleanup_clean"]
            and not report["errors"]
        )
        receipts = {}
        for path in sorted(output.iterdir()):
            if path.is_file():
                receipts[path.name] = {
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
        report["receipts"] = receipts
        (output / "result.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
