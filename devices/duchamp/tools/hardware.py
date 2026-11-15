#!/usr/bin/env python3
"""Extract selected MT6897 hardware facts from the pinned saved FDT; no I/O.

This is a configuration generator, not an ownership grant or a raw DTB export.
It emits no chosen bootargs, identifiers, credentials or firmware bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct

REPO = Path(__file__).resolve().parents[3]
FDT_SHA = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"


def extract(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FDT_SHA:
        raise ValueError("Duchamp FDT digest differs; review a new capture independently")
    tree = runpy.run_path(str(REPO / "tools/inspect-duchamp-hardware.py"))["Fdt"](raw)
    def node(n):
        result = dict(path=n.path, compatible=n.strings("compatible"),
                      status=n.strings("status") or ["okay (DT default)"],
                      register_access="UNKNOWN", resource_ownership_at_xnu="UNKNOWN")
        if "reg" in n.props:
            try:
                result["reg"] = tree.registers(n)
            except ValueError as error:
                result["reg"] = dict(state="UNKNOWN", reason=str(error))
        else:
            result["reg"] = "UNKNOWN"
        for key in ("clocks", "resets", "power-domains", "phys", "iommus"):
            if key not in n.props:
                result[key] = "UNKNOWN"
                continue
            count = {"clocks": "#clock-cells", "resets": "#reset-cells",
                     "power-domains": "#power-domain-cells", "phys": "#phy-cells",
                     "iommus": "#iommu-cells"}[key]
            try:
                result[key] = tree.references(n, key, count)
            except ValueError as error:
                result[key] = dict(state="UNKNOWN", reason=str(error))
        for key in ("interrupts", "interrupts-extended", "dma-ranges", "reg-names"):
            if key in n.props:
                result[key] = n.strings(key) if key == "reg-names" else n.cells(key)
        if "interrupts" in n.props or "interrupts-extended" in n.props:
            try:
                result["resolved_interrupts"] = tree.interrupts(n)
            except ValueError as error:
                result["resolved_interrupts"] = dict(state="UNKNOWN", reason=str(error))
        result["supplies"] = {k: tree.provider(n.scalar(k)).path for k in n.props if k.endswith("-supply")}
        if "clock-frequency" in n.props:
            result["clock_frequency_hz"] = n.scalar("clock-frequency")
        return result
    groups = {name: [] for name in ("ram", "reserved_memory", "gic", "timer", "uart", "ufs",
              "ufs_phy", "spi2_touch", "gpu", "usb", "display", "power", "iommu")}
    for n in tree.nodes.values():
        c = " ".join(n.strings("compatible"))
        names = []
        if n.strings("device_type") == ["memory"]: names.append("ram")
        if n.path.startswith("/reserved-memory/"): names.append("reserved_memory")
        if "arm,gic-v3" in c: names.append("gic")
        if "arm,armv8-timer" in c: names.append("timer")
        if "mt6577-uart" in c: names.append("uart")
        if "ufshci" in c: names.append("ufs")
        if "ufsphy" in c: names.append("ufs_phy")
        if n.path.startswith("/soc/spi2@"): names.append("spi2_touch")
        if any(s in c for s in ("mali", "mfgcfg")): names.append("gpu")
        if any(s in c for s in ("usb", "ssusb", "dwc3")): names.append("usb")
        if any(s in c for s in ("mediatek,mt6897-disp", "lcm", "mediatek,framebuffer")): names.append("display")
        if any(s in c for s in ("pmif", "pmic", "pwrap", "scpsys")): names.append("power")
        if any(s in c for s in ("iommu", "smmu")): names.append("iommu")
        if names:
            value = node(n)
            for name in names: groups[name].append(value)
    reserve = struct.unpack_from(">I", raw, 16)[0]
    memreserve = []
    while True:
        address, size = struct.unpack_from(">QQ", raw, reserve); reserve += 16
        if not address and not size: break
        memreserve.append(dict(address=hex(address), bytes=hex(size)))
    return dict(schema=1, device="duchamp", soc="mt6897", fdt_sha256=FDT_SHA,
                evidence="saved live Android FDT; declarations are not XNU runtime grants",
                memreserve=memreserve, hardware=groups,
                existing_profile_source="duchamp/loader/mt6897_platform.c",
                unknown={k: dict(value="UNKNOWN", obtain=how) for k, how in {
                    "ufs_resource_lease": "verified same-boot initialization or documented LK/firmware handoff",
                    "dma_cache_owner": "validate actual DMA route, system-cache owner and XNU cache operations",
                    "android_chainboot": "validate v4 Android/vendor_boot handoff and recovery before any phone experiment",
                    "retained_pmsg": "prove layout and retention across the actual selected reset",
                    "display_cold_init": "document panel, clocks, rails and IOMMU; inherited framebuffer is insufficient",
                    "dtbo_applicability": "compare a pinned stock DTBO with the final captured FDT"}.items()},
                physical_enable=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dtb", type=Path); ap.add_argument("output", type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = json.dumps(extract(args.dtb), indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.output.read_text() != data: raise SystemExit("Hardware configuration differs")
    else:
        with args.output.open("x") as stream: stream.write(data)
