#!/usr/bin/env python3
"""Capture read-only MT6897 UFS provider bindings from a running Duchamp.

The capture is intentionally attribution-only.  It reads sysfs, procfs and
Android properties through ADB, but never writes a phone file, changes a
driver, executes an SMC, accesses MMIO, or touches a block device.  Linux
driver bindings are not treated as delegation to XNU.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess


REPORT_VERSION = 1

EXPECTED_BINDINGS = {
    "emi_slb_observer": {
        "path": "/sys/bus/platform/devices/10342000.emislb",
        "driver": "/sys/bus/platform/drivers/emislb_driver",
        "runtime_status": "unsupported",
    },
    "ufs_hci": {
        "path": "/sys/bus/platform/devices/112b0000.ufshci",
        "driver": "/sys/bus/platform/drivers/ufshcd-mtk",
        "runtime_status": "active",
    },
    "ufs_phy": {
        "path": "/sys/bus/platform/devices/112a0000.ufsphy",
        "driver": "/sys/bus/platform/drivers/ufs_mtk_phy",
        "runtime_status": "active",
    },
    "topckgen": {
        "path": "/sys/bus/platform/devices/10000000.syscon",
        "driver": "/sys/bus/platform/drivers/clk-mt6897",
        "runtime_status": "unsupported",
    },
    "ufs_clock_ao": {
        "path": "/sys/bus/platform/devices/112b8000.syscon",
        "driver": "/sys/bus/platform/drivers/clk-mt6897-peri",
        "runtime_status": "unsupported",
    },
    "ufs_clock_reset_pdn": {
        "path": "/sys/bus/platform/devices/112bb000.syscon",
        "driver": "/sys/bus/platform/drivers/clk-mt6897-peri",
        "runtime_status": "unsupported",
    },
    "dvfsrc": {
        "path": "/sys/bus/platform/devices/1c00f000.dvfsrc",
        "driver": "/sys/bus/platform/drivers/mtk-dvfsrc",
        "runtime_status": "unsupported",
    },
    "secure_power_controller": {
        "path": "/sys/bus/platform/devices/1c001000.power-controller",
        "driver": "/sys/bus/platform/drivers/mtk-scpsys-mt6897",
        "runtime_status": "unsupported",
    },
}

HW_VOTER_PATH = "/sys/bus/platform/devices/10320000.syscon"
HW_VOTER_COMPATIBLES = ("mediatek,mt6897-hwv", "syscon")

EXPECTED_REGULATORS = {
    "mt6363_vemc": {"state": "enabled", "microvolts": 2500000},
    "8_vbuck3": {"state": "enabled", "microvolts": 1193750},
    "dvfsrc-vcore": {"microvolts": 800000},
}

REQUIRED_MODULES = {
    "cache_and_slc": (
        "emi_slb", "slbc_mt6897", "slbc_ipi", "mtk_slbc", "tinysys_scmi",
    ),
    "firewall_and_protection": (
        "smpu", "emi_mpu", "device_apc_mt6897", "device_apc_common",
    ),
    "ufs_and_resources": (
        "ufs_mediatek_mod", "phy_mtk_ufs", "clk_mt6897",
        "clk_mt6897_peri", "mtk_scpsys_mt6897", "mtk_dvfsrc",
    ),
}

UFS_DEVICE = "/sys/devices/platform/soc/112b0000.ufshci"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_modules(raw):
    modules = {}
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) >= 6:
            modules[fields[0]] = {
                "bytes": int(fields[1]),
                "refcount": int(fields[2]),
                "state": fields[-3],
                "taints": fields[-1].strip("()"),
            }
    return modules


def parse_compatibles(raw):
    return [value for value in raw.split("\0") if value]


def parse_ufs_interrupts(raw):
    rows = []
    for line in raw.splitlines():
        if "ufshcd" not in line:
            continue
        fields = line.split()
        require(fields and fields[0].endswith(":"), "invalid UFS IRQ row")
        irq = int(fields[0][:-1])
        gic_index = fields.index("GICv3")
        hwirq = int(fields[gic_index + 1])
        trigger = fields[gic_index + 2]
        rows.append({
            "linux_irq": irq,
            "gic_hwirq": hwirq,
            "trigger": trigger,
            "handler": fields[-1],
        })
    return rows


def analyze_snapshot(snapshot):
    require(snapshot.get("device") == "duchamp", "unexpected product device")
    require(snapshot.get("hardware") == "mt6897", "unexpected boot hardware")
    require(snapshot.get("slot_suffix") in ("_a", "_b"),
            "unexpected active slot")
    require(snapshot.get("root_id", "").startswith("uid=0(root)"),
            "ADB root shell was not proven")

    observed_bindings = snapshot.get("bindings", {})
    binding_report = {}
    for resource_id, expected in EXPECTED_BINDINGS.items():
        observed = observed_bindings.get(resource_id, {})
        require(observed.get("path") == expected["path"],
                resource_id + " path differs")
        require(observed.get("driver") == expected["driver"],
                resource_id + " driver differs")
        require(observed.get("runtime_status") == expected["runtime_status"],
                resource_id + " runtime status differs")
        binding_report[resource_id] = {
            **observed,
            "linux_driver_binding_proven": True,
            "exclusive_owner_proven": False,
            "xnu_delegation_proven": False,
        }

    hw_voter = snapshot.get("hw_voter", {})
    require(hw_voter.get("path") == HW_VOTER_PATH,
            "hardware voter path differs")
    require(tuple(hw_voter.get("compatibles", [])) == HW_VOTER_COMPATIBLES,
            "hardware voter compatible differs")
    require(hw_voter.get("driver") is None,
            "hardware voter unexpectedly gained a standalone driver")

    regulator_report = {}
    observed_regulators = snapshot.get("regulators", {})
    require(set(observed_regulators) == set(EXPECTED_REGULATORS),
            "UFS regulator set differs")
    for name, expected in EXPECTED_REGULATORS.items():
        observed = observed_regulators[name]
        require(observed.get("microvolts") == expected["microvolts"],
                name + " voltage differs")
        if "state" in expected:
            require(observed.get("state") == expected["state"],
                    name + " state differs")
        regulator_report[name] = {
            **observed,
            "linux_runtime_state_observed": True,
            "xnu_delegation_proven": False,
        }

    modules = parse_modules(snapshot.get("proc_modules", ""))
    module_groups = {}
    for group, names in REQUIRED_MODULES.items():
        missing = [name for name in names if name not in modules]
        require(not missing, group + " modules missing: " + ", ".join(missing))
        module_groups[group] = {
            "required": list(names),
            "all_loaded": True,
        }

    irq_rows = parse_ufs_interrupts(snapshot.get("proc_interrupts", ""))
    require(len(irq_rows) == 9, "expected nine UFS IRQ rows")
    require(tuple(row["gic_hwirq"] for row in irq_rows) ==
            (200, 209, 210, 211, 212, 213, 214, 215, 216),
            "UFS GIC HWIRQ mapping differs")
    require(all(row["trigger"] == "Level" and row["handler"] == "ufshcd"
                for row in irq_rows), "UFS IRQ handler differs")

    supplier_links = sorted(snapshot.get("supplier_links", []))
    require(len(supplier_links) == 13, "UFS supplier-link count differs")
    require(any("112a0000.ufsphy" in value for value in supplier_links),
            "UFS PHY supplier link missing")
    require(any("10000000.syscon" in value for value in supplier_links),
            "topckgen supplier link missing")
    require(any("reset-controller" in value for value in supplier_links),
            "reset supplier link missing")
    require(sum("supplier:regulator:" in value for value in supplier_links) == 3,
            "regulator supplier-link count differs")
    require(not any("10342000" in value or "slbc" in value.lower() or
                    "system-cache" in value.lower()
                    for value in supplier_links),
            "UFS unexpectedly gained an SLB/system-cache supplier link")

    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "target": {
            "device": snapshot["device"],
            "soc": snapshot["hardware"],
            "active_slot": snapshot["slot_suffix"],
            "serial_sha256": hashlib.sha256(
                snapshot.get("serial", "").encode("utf-8")
            ).hexdigest(),
        },
        "linux_runtime": {
            "bindings": binding_report,
            "hw_voter": {
                **hw_voter,
                "syscon_declaration_observed": True,
                "standalone_driver_binding_proven": False,
                "xnu_delegation_proven": False,
            },
            "regulators": regulator_report,
            "module_groups": module_groups,
            "ufs_supplier_links": supplier_links,
            "ufs_interrupts": irq_rows,
            "provider_bindings_proven": True,
            "ufs_irq_handler_binding_proven": True,
        },
        "proof_boundary": {
            "linux_current_provider_bindings_proven": True,
            "linux_ufs_regulator_state_observed": True,
            "linux_ufs_irq_handler_binding_proven": True,
            "slb_and_scmi_coordination_modules_loaded": True,
            "firewall_and_protection_modules_loaded": True,
            "system_cache_exclusive_owner_proven": False,
            "ufs_cache_maintenance_reachability_proven": False,
            "runtime_smc_effect_proven": False,
            "firewall_state_or_ufs_grant_proven": False,
            "xnu_mmio_clock_reset_phy_regulator_irq_delegation_proven": False,
            "installed_firmware_byte_equivalence_proven": False,
        },
        "authorization": {
            "physical_backend_enabled": False,
            "mmio_callbacks": 0,
            "smc_callbacks": 0,
            "dma_callbacks": 0,
            "ufs_commands": 0,
            "interrupt_reconfiguration_callbacks": 0,
        },
        "capture": {
            "captured_at_utc": snapshot.get("captured_at_utc"),
            "adb_root": True,
            "read_only_queries": True,
        },
        "safety": {
            "phone_read": True,
            "phone_write": False,
            "selinux_policy_change": False,
            "module_load": False,
            "mmio_access": False,
            "smc_execution": False,
            "firewall_probe": False,
            "block_device_access": False,
            "partition_write": False,
            "physical_ufs_backend_enabled": False,
        },
        "scope": (
            "read-only Linux provider attribution; bindings and loaded modules "
            "do not delegate any resource or firmware ABI to XNU"
        ),
    }


class AdbReader:
    def __init__(self, adb, serial=None):
        self.adb = str(adb)
        self.serial = serial

    def _run(self, args):
        command = [self.adb]
        if self.serial:
            command += ["-s", self.serial]
        command += args
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        stdout = result.stdout.decode("utf-8", errors="surrogateescape")
        stderr = result.stderr.decode("utf-8", errors="replace")
        if result.returncode:
            raise ValueError(
                "ADB read failed: " + " ".join(args) + ": " + stderr.strip()
            )
        return stdout.rstrip("\r\n")

    def shell(self, command, root=False):
        if root:
            return self._run(["shell", "su", "-c", command])
        return self._run(["shell", command])

    def getprop(self, name):
        return self.shell("getprop " + shlex.quote(name)).strip()

    def cat(self, path):
        return self.shell("cat " + shlex.quote(path), root=True)

    def cat_optional(self, path):
        try:
            return self.cat(path)
        except ValueError:
            return None

    def readlink(self, path, allow_missing=False):
        if allow_missing:
            try:
                self.shell("readlink " + shlex.quote(path), root=True)
            except ValueError:
                return None
        try:
            value = self.shell("readlink -f " + shlex.quote(path), root=True)
        except ValueError:
            if allow_missing:
                return None
            raise
        return value


def capture_snapshot(reader):
    if reader.serial is None:
        devices = reader._run(["devices"]).splitlines()[1:]
        attached = [line.split()[0] for line in devices
                    if line.strip().endswith("\tdevice")]
        require(len(attached) == 1, "select exactly one ADB device")
        reader.serial = attached[0]

    bindings = {}
    for resource_id, expected in EXPECTED_BINDINGS.items():
        path = expected["path"]
        bindings[resource_id] = {
            "path": path,
            "driver": reader.readlink(path + "/driver"),
            "runtime_status": reader.cat(path + "/power/runtime_status").strip(),
        }

    hw_voter_compatible = reader.cat(
        HW_VOTER_PATH + "/of_node/compatible"
    )
    hw_voter = {
        "path": HW_VOTER_PATH,
        "compatibles": parse_compatibles(hw_voter_compatible),
        "driver": reader.readlink(HW_VOTER_PATH + "/driver", allow_missing=True),
    }

    supplier_raw = reader.shell(
        "ls -1d " + shlex.quote(UFS_DEVICE + "/supplier:") + "*",
        root=True,
    )
    supplier_links = sorted(line.strip() for line in supplier_raw.splitlines()
                            if line.strip())
    regulator_ids = sorted({
        match.group(1)
        for line in supplier_links
        for match in [re.search(r"supplier:regulator:regulator\.(\d+)$", line)]
        if match
    }, key=int)
    regulators = {}
    for regulator_id in regulator_ids:
        base = "/sys/class/regulator/regulator." + regulator_id
        name = reader.cat(base + "/name").strip()
        state_raw = reader.cat_optional(base + "/state")
        state = state_raw.strip() if state_raw is not None else ""
        regulators[name] = {
            "sysfs_id": int(regulator_id),
            "state": state or None,
            "microvolts": int(reader.cat(base + "/microvolts").strip()),
            "device": reader.readlink(base + "/device"),
        }

    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "serial": reader.serial,
        "device": reader.getprop("ro.product.device"),
        "hardware": reader.getprop("ro.boot.hardware"),
        "slot_suffix": reader.getprop("ro.boot.slot_suffix"),
        "root_id": reader.shell("id", root=True),
        "bindings": bindings,
        "hw_voter": hw_voter,
        "regulators": regulators,
        "supplier_links": supplier_links,
        "proc_modules": reader.cat("/proc/modules"),
        "proc_interrupts": reader.cat("/proc/interrupts"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--serial")
    parser.add_argument("--snapshot", type=Path,
                        help="analyze a previously saved synthetic snapshot")
    args = parser.parse_args()

    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    if args.snapshot:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    else:
        snapshot = capture_snapshot(AdbReader(args.adb, args.serial))
    report = analyze_snapshot(snapshot)

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "passed": True,
        "output": str(output),
        "provider_bindings_proven": True,
        "xnu_delegation_proven": False,
        "physical_backend_enabled": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
