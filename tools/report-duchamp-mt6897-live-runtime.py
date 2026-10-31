#!/usr/bin/env python3
"""Verify read-only Duchamp runtime captures without touching the phone.

The capture itself is produced separately.  This tool only reads local files,
matches DT interrupt declarations to Linux's GICv3 runtime view, and keeps
Linux observations separate from claims about XNU or physical DMA ownership.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


REQUIRED_FILES = (
    "live-fdt.bin",
    "interrupts-1.txt",
    "interrupts-2.txt",
    "clocksource-current.txt",
    "clockevent-current.txt",
    "ufs-driver.txt",
    "ufs-iommu-group-probe.txt",
    "ufs-iommu-group-probe.stderr.txt",
    "ufs-iommu-group-probe.exit.txt",
    "scmi-platform-driver.txt",
    "cpuidle-current-driver.txt",
)

# These values are populated by the bootloader/fuel-gauge at runtime.  They
# are not part of the GIC, timer, firmware, UFS, PHY, clock or DMA topology.
ALLOWED_RUNTIME_FDT_CHANGES = {
    ("/bootprof", "lk_t"),
    ("/bootprof", "pl_t"),
    ("/bootprof", "sec_os_t"),
    ("/i2c@11f01000/mt6375@34/mtk-gauge", "fg_swocv_i"),
    ("/i2c@11f01000/mt6375@34/mtk-gauge", "fg_swocv_v"),
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_fdt_parser(repo):
    path = repo / "tools/inspect-duchamp-hardware.py"
    spec = importlib.util.spec_from_file_location("duchamp_live_fdt", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load FDT parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_text(path):
    return path.read_text(encoding="utf-8", errors="strict").strip()


def parse_interrupts(text):
    lines = text.splitlines()
    if not lines:
        raise ValueError("empty /proc/interrupts capture")
    cpu_count = len(re.findall(r"\bCPU\d+\b", lines[0]))
    if not 1 <= cpu_count <= 256:
        raise ValueError("invalid CPU header in /proc/interrupts capture")
    rows = {}
    for line in lines[1:]:
        match = re.match(r"\s*(\d+):\s+(.*)", line)
        if not match:
            continue
        fields = match.group(2).split()
        if len(fields) < cpu_count or not all(
            field.isdecimal() for field in fields[:cpu_count]
        ):
            continue
        irq = int(match.group(1))
        if irq in rows:
            raise ValueError(f"duplicate Linux IRQ {irq}")
        rows[irq] = {
            "counts": [int(field) for field in fields[:cpu_count]],
            "tail": fields[cpu_count:],
        }
    return cpu_count, rows


def gic_row(row):
    tail = row["tail"]
    if len(tail) < 4 or tail[0] != "GICv3" or not tail[1].isdecimal():
        return None
    return {
        "controller": tail[0],
        "hwirq": int(tail[1]),
        "trigger": tail[2],
        "name": " ".join(tail[3:]),
    }


def interrupt_deltas(before_text, after_text):
    before_cpus, before = parse_interrupts(before_text)
    after_cpus, after = parse_interrupts(after_text)
    if before_cpus != after_cpus:
        raise ValueError("CPU count changed between interrupt captures")
    result = []
    for irq in sorted(set(before) & set(after)):
        if before[irq]["tail"] != after[irq]["tail"]:
            raise ValueError(f"Linux IRQ {irq} identity changed between captures")
        delta = [
            end - start
            for start, end in zip(before[irq]["counts"], after[irq]["counts"])
        ]
        if any(value < 0 for value in delta):
            raise ValueError(f"Linux IRQ {irq} counter moved backwards")
        identity = gic_row(after[irq])
        if identity:
            result.append(
                {
                    "linux_irq": irq,
                    **identity,
                    "per_cpu_delta": delta,
                    "total_delta": sum(delta),
                }
            )
    return before_cpus, result


def fdt_snapshot(tree):
    return {
        path: {name: sha256(value) for name, value in node.props.items()}
        for path, node in tree.nodes.items()
    }


def compare_fdt(reference, live):
    old = fdt_snapshot(reference)
    new = fdt_snapshot(live)
    added_nodes = sorted(set(new) - set(old))
    removed_nodes = sorted(set(old) - set(new))
    changed = []
    for path in sorted(set(old) & set(new)):
        for prop in sorted(set(old[path]) | set(new[path])):
            if old[path].get(prop) != new[path].get(prop):
                changed.append((path, prop))
    unexpected = [
        {"path": path, "property": prop}
        for path, prop in changed
        if (path, prop) not in ALLOWED_RUNTIME_FDT_CHANGES
    ]
    if added_nodes or removed_nodes or unexpected:
        raise ValueError(
            "live FDT has unexpected topology/property changes: "
            f"added={added_nodes}, removed={removed_nodes}, changed={unexpected}"
        )
    return {
        "node_count": len(new),
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "allowed_runtime_changes": [
            {"path": path, "property": prop} for path, prop in changed
        ],
        "critical_topology_matches_reference": True,
    }


def ancestor_dma_contract(node):
    result = []
    while node:
        result.append(
            {
                "path": node.path,
                "iommus_present": "iommus" in node.props,
                "iommu_map_present": "iommu-map" in node.props,
                "dma_coherent_present": "dma-coherent" in node.props,
                "dma_ranges_cells": node.cells("dma-ranges"),
            }
        )
        node = node.parent
    return result


def file_receipts(evidence):
    receipts = {}
    for name in REQUIRED_FILES:
        path = evidence / name
        raw = path.read_bytes()
        receipts[name] = {"bytes": len(raw), "sha256": sha256(raw)}
    return receipts


def build_report(evidence, reference_dtb, repo):
    evidence = Path(evidence).resolve()
    repo = Path(repo).resolve()
    missing = [name for name in REQUIRED_FILES if not (evidence / name).is_file()]
    if missing:
        raise ValueError(f"missing evidence files: {missing}")

    parser = load_fdt_parser(repo)
    live_raw = (evidence / "live-fdt.bin").read_bytes()
    live = parser.Fdt(live_raw)
    if live.nodes["/"].strings("model") != ["MT6897"]:
        raise ValueError("live FDT root model is not MT6897")
    reference_raw = Path(reference_dtb).read_bytes()
    reference = parser.Fdt(reference_raw)
    equivalence = compare_fdt(reference, live)

    gic = live.nodes.get("/interrupt-controller")
    timer = live.nodes.get("/timer")
    ufs = live.nodes.get("/soc/ufshci@112b0000")
    psci = live.nodes.get("/psci")
    scmi = live.nodes.get("/firmware/scmi")
    if not all((gic, timer, ufs, psci, scmi)):
        raise ValueError("required GIC/timer/UFS/PSCI/SCMI node is missing")
    if "arm,gic-v3" not in gic.strings("compatible"):
        raise ValueError("primary interrupt controller is not GICv3")
    if "arm,armv8-timer" not in timer.strings("compatible"):
        raise ValueError("architected timer node is missing")
    if "mediatek,mt8183-ufshci" not in ufs.strings("compatible"):
        raise ValueError("unexpected UFS host compatible")

    ufs_interrupts = parser.Fdt.interrupts(live, ufs)
    if any(entry["provider"] != "/interrupt-controller" for entry in ufs_interrupts):
        raise ValueError("UFS interrupt is not routed through the primary GIC")
    dt_ufs_spis = []
    for entry in ufs_interrupts:
        args = entry["args"]
        if len(args) != 4 or args[0] != 0:
            raise ValueError(f"unsupported UFS interrupt tuple: {args}")
        dt_ufs_spis.append(args[1])
    expected_ufs_hwirqs = sorted(spi + 32 for spi in dt_ufs_spis)

    cpu_count, deltas = interrupt_deltas(
        read_text(evidence / "interrupts-1.txt"),
        read_text(evidence / "interrupts-2.txt"),
    )
    timer_rows = [row for row in deltas if row["name"] == "arch_timer"]
    if len(timer_rows) != 1 or timer_rows[0]["hwirq"] != 27:
        raise ValueError("expected one GICv3 arch_timer row at PPI 27")
    ufs_rows = [row for row in deltas if row["name"] == "ufshcd"]
    runtime_ufs_hwirqs = sorted(row["hwirq"] for row in ufs_rows)
    if runtime_ufs_hwirqs != expected_ufs_hwirqs:
        raise ValueError(
            "UFS DT/runtime IRQ mismatch: "
            f"expected {expected_ufs_hwirqs}, got {runtime_ufs_hwirqs}"
        )
    timer_delta = timer_rows[0]["total_delta"]
    ufs_delta = sum(row["total_delta"] for row in ufs_rows)
    if timer_delta <= 0:
        raise ValueError("no architected-timer interrupt progress observed")
    if ufs_delta <= 0:
        raise ValueError("no UFS interrupt progress observed")

    clocksource = read_text(evidence / "clocksource-current.txt")
    clockevent = read_text(evidence / "clockevent-current.txt")
    driver = read_text(evidence / "ufs-driver.txt").replace("\\", "/")
    cpuidle = read_text(evidence / "cpuidle-current-driver.txt")
    if clocksource != "arch_sys_counter" or clockevent != "arch_sys_timer":
        raise ValueError(f"unexpected clocksource/event: {clocksource}/{clockevent}")
    if not driver.endswith("/ufshcd-mtk"):
        raise ValueError(f"unexpected UFS driver: {driver}")
    if cpuidle != "psci_idle":
        raise ValueError(f"unexpected CPU idle driver: {cpuidle}")

    iommu_exit = int(read_text(evidence / "ufs-iommu-group-probe.exit.txt"))
    iommu_stdout = read_text(evidence / "ufs-iommu-group-probe.txt")
    iommu_stderr = read_text(evidence / "ufs-iommu-group-probe.stderr.txt")
    if iommu_exit == 0:
        sysfs_iommu_group = bool(iommu_stdout)
    elif iommu_exit == 1 and not iommu_stdout and "No such file" in iommu_stderr:
        sysfs_iommu_group = False
    else:
        raise ValueError("ambiguous UFS iommu_group probe result")

    ancestry = ancestor_dma_contract(ufs)
    dt_iommu_binding = any(
        item["iommus_present"] or item["iommu_map_present"] for item in ancestry
    )
    scmi_bound = "firmware:scmi" in read_text(
        evidence / "scmi-platform-driver.txt"
    )
    if not scmi_bound:
        raise ValueError("arm-scmi platform binding was not observed")

    return {
        "report_version": 1,
        "evidence": file_receipts(evidence),
        "fdt": {
            "live_sha256": sha256(live_raw),
            "reference_sha256": sha256(reference_raw),
            **equivalence,
        },
        "runtime": {
            "cpu_count": cpu_count,
            "gic": {
                "compatible": gic.strings("compatible"),
                "registers": live.registers(gic),
                "linux_controller_observed": "GICv3",
            },
            "timer": {
                "clocksource": clocksource,
                "clockevent": clockevent,
                "linux_irq": timer_rows[0]["linux_irq"],
                "gic_hwirq": timer_rows[0]["hwirq"],
                "per_cpu_delta": timer_rows[0]["per_cpu_delta"],
                "total_delta": timer_delta,
                "android_runtime_delivery_observed": True,
                "xnu_phone_delivery_observed": False,
            },
            "ufs": {
                "driver": driver,
                "dt_spi_ids": dt_ufs_spis,
                "expected_gic_hwirqs": expected_ufs_hwirqs,
                "irq_rows": ufs_rows,
                "total_delta": ufs_delta,
                "android_runtime_delivery_observed": True,
                "xnu_phone_delivery_observed": False,
            },
        },
        "firmware": {
            "psci_compatible": psci.strings("compatible"),
            "psci_method": psci.strings("method"),
            "linux_cpuidle_driver": cpuidle,
            "scmi_compatible": scmi.strings("compatible"),
            "scmi_mailboxes_present": "mboxes" in scmi.props,
            "scmi_shared_memory_present": "shmem" in scmi.props,
            "linux_scmi_platform_binding_observed": scmi_bound,
            "xnu_firmware_abi_verified": False,
            "physical_resource_ownership_verified": False,
        },
        "dma": {
            "ufs_ancestry": ancestry,
            "dt_iommu_binding_declared": dt_iommu_binding,
            "linux_sysfs_iommu_group_attached": sysfs_iommu_group,
            "linux_observation": (
                "no DT IOMMU binding or Linux iommu_group attachment observed"
                if not dt_iommu_binding and not sysfs_iommu_group
                else "an IOMMU declaration or Linux attachment was observed"
            ),
            "physical_dma_bypass_verified": False,
            "coherency_verified": False,
            "xnu_dma_ready": False,
        },
        "result": {
            "passed": True,
            "proven": [
                "Android uses GICv3 and the architected ARM timer at runtime",
                "the captured UFS DT IRQ tuples match Linux ufshcd IRQs",
                "UFS interrupt progress occurred through ufshcd-mtk",
                "Linux bound arm-scmi and uses psci_idle",
            ],
            "not_proven": [
                "XNU timer or interrupt delivery on the physical phone",
                "XNU ownership of GIC or installed firmware ABIs",
                "physical UFS DMA bypass, coherency, or firewall permissions",
                "safe physical UFS access from XNU",
            ],
        },
        "safety": {
            "offline_analysis_only": True,
            "read_only_inputs": True,
            "adb_access_by_this_tool": False,
            "mmio_access": False,
            "phone_write": False,
            "partition_access": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path, help="local read-only capture directory")
    parser.add_argument("reference_dtb", type=Path, help="previous exact Duchamp DTB")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        report = build_report(args.evidence, args.reference_dtb, repo)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"live runtime report failed: {error}\n")
    print(
        json.dumps(
            report,
            indent=None if args.compact else 2,
            separators=(",", ":") if args.compact else None,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
