#!/usr/bin/env python3
"""Corroborate saved Duchamp allocation evidence. Offline files only.

No device transports, MMIO, grants, image rebuilding, or authorization output.
The pinned archives are historical; all candidate decisions remain blocked.
"""

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from duchamp_mblock import decode_mblock
from duchamp_memory_placement import (BOOT_PHASES, Interval, check_boot_lifetimes,
                                       check_candidate, coverage_by_banks)


PINS = {
    "lk": "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a",
    "fdt": "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29",
    "retained_log": "bee2a8bd4a06b44fdb8b88b8d6957e30721ab52051da91425b72684a1c3aa18d",
    "reference_map": "9a07f42c09d05a610af5d52a6bfeefe6341bf48d6cefe223b9b6ea90071799a7",
}
LK_VA = 0xffff000050700000


def load_fdt(raw):
    path = Path(__file__).with_name("inspect-duchamp-hardware.py")
    spec = importlib.util.spec_from_file_location("duchamp_saved_hardware", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.Fdt(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in PINS:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs, receipt = {}, {}
    for name, expected in PINS.items():
        path = getattr(args, name)
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"{name} differs from audited archive")
        inputs[name] = raw
        receipt[name] = {"path": str(path.resolve()), "bytes": len(raw), "sha256": actual}
    args.output.mkdir(parents=True, exist_ok=True)
    tree = load_fdt(inputs["fdt"])
    mblock = decode_mblock(tree.nodes["/memory"].props["mblock_info"])
    fixed = []
    for path, node in tree.nodes.items():
        if not path.startswith("/reserved-memory/mblock-"):
            continue
        if len(node.props["reg"]) != 16:
            raise ValueError("unexpected fixed FDT reservation format")
        start, size = struct.unpack(">QQ", node.props["reg"])
        name = re.fullmatch(r"mblock-\d+-(.+)", path.rsplit("/", 1)[1]).group(1)
        fixed.append((name, start, size, 0 if "no-map" in node.props else 1))
    decoded = [(row["name"], row["start"], row["bytes"], row["mapping"])
               for row in mblock["reserved"]]
    if sorted(fixed) != sorted(decoded) or len(fixed) != 52:
        raise ValueError("mblock entries disagree with FDT reservations")
    memory_map = json.loads(inputs["reference_map"])
    reference = next(row for row in memory_map["candidates"] if row["name"] == "native-4m-var")
    if reference["volumes"]["var"]["bytes"] != 4 * 1024 * 1024:
        raise ValueError("reference must have a 4 MiB writable RAM disk")
    mblock["matches_fixed_fdt_entries"] = len(fixed)
    mblock["reference_extents"] = {}
    for name, interval in (
            ("lk-output", Interval(reference["image"]["load_pa"], reference["image"]["end_pa"])),
            ("xnu-window", Interval.from_row(reference["xnu_window"]))):
        mblock["reference_extents"][name] = {
            "within_archived_free_pool": coverage_by_banks(interval, sorted(
                (Interval.from_row(row) for row in mblock["free"]), key=lambda row: row.start)),
            "current_ownership_proven": False}

    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    decoded_instructions = {}
    ranges = (("loader-output-and-release", 0xfd00, 0x10074),
              ("decompressor", 0xe928, 0xecb0),
              ("mblock-query", 0x151b8, 0x152b8),
              ("mblock-release", 0x15688, 0x15780),
              ("fdt-mblock-property", 0x16654, 0x166d8),
              ("mblock-reserved-stride", 0x16280, 0x16344),
              ("image-input-getter", 0xcd50, 0xcda4))
    for name, start, end in ranges:
        lines = []
        for ins in md.disasm(inputs["lk"][start:end], LK_VA + start - 0x200):
            offset = ins.address - LK_VA + 0x200
            decoded_instructions[offset] = (ins.mnemonic, ins.op_str)
            lines.append(f"file+0x{offset:x}: {ins.mnemonic} {ins.op_str}")
        (args.output / (name + ".disasm")).write_text("\n".join(lines) + "\n")
    expected = {
        0xfd38: ("ldp", "x4, x20, [x0]"),
        0xfda0: ("ldur", "x1, [x29, #-0x18]"),
        0xfdb0: ("bl", "#0xffff00005070e728"),
        0xfeac: ("bl", "#0xffff000050715488"),
        0xfeb4: ("bl", "#0xffff000050715488"),
        0xfebc: ("bl", "#0xffff000050715488"),
        0xfed8: ("bl", "#0xffff000050715fc8"),
        0x16688: ("mov", "w4, #0x5818"),
        0x16284: ("add", "x28, x8, #0xc18"),
        0x16330: ("add", "x28, x28, #0x98"),
        0x166b4: ("mov", "w10, #0x18"),
    }
    for offset, instruction in expected.items():
        if decoded_instructions.get(offset) != instruction:
            raise ValueError(f"LK instruction not corroborated at file+0x{offset:x}")
    strings = {"mblock_source_path": (0xc31a9, "lib/mblock/mblock.c"),
               "loader_function": (0xbe469, "boot_linux_fdt"),
               "kernel_reservation": (0xb5221, "mb_kernel"),
               "lk_reservation": (0xc54d8, "BL33-reserved"),
               "fdt_property": (0xaf79b, "mblock_info")}
    for name, (offset, expected_string) in strings.items():
        if inputs["lk"][offset:].split(b"\0", 1)[0].decode() != expected_string:
            raise ValueError("LK string binding mismatch: " + name)
    lk_evidence = {"scope": "binary-intent-only-not-execution-proof",
                   "instruction_checks": len(expected), "strings": {
                       name: {"partition_file_offset": offset, "value": value}
                       for name, (offset, value) in strings.items()},
                   "release_return_values_proven": False,
                   "compressed_input_and_scratch_final_extent_proven": False,
                   "final_dma_exclusion_proven": False}

    lines = inputs["retained_log"].decode(errors="replace").splitlines()
    selected = [{"line": index, "text": line} for index, line in enumerate(lines, 1)
                if re.search(r"mb_kernel|mb_dtb|BL33-reserved|md_mem_usage|ccci_tag_mem|"
                             r"system_fastboot_buffer|kernel jump|jump to kernel", line)]
    (args.output / "retained-allocation-extract.json").write_text(json.dumps(selected, indent=2) + "\n")
    if not any("mb_kernel" in row["text"] and "0x40000000" in row["text"] and
               "0x7c80000" in row["text"] for row in selected):
        raise ValueError("retained log lacks the expected kernel reservation")

    def span(name, role, start, size, first, last, alignment=0x1000):
        return {"name": name, "role": role, "start": start, "bytes": size,
                "alignment": alignment, "length_alignment": 1,
                "first_phase": first, "last_phase": last}

    initial, finalize, bl31, copy_phase, runtime = BOOT_PHASES
    buffers = [
        span("LK compressed input", "compressed-input", None,
             reference["envelope"]["compressed_image_bytes"], initial, initial),
        span("LK decompression scratch", "decompression-scratch", None, None, initial, initial),
        span("LK decompressed Image", "lk-output", reference["image"]["load_pa"],
             reference["image"]["bytes"], initial, copy_phase),
        span("Incoming FDT reservation", "fdt", 0x47c80000, 0x400000, initial, copy_phase),
        span("XNU runtime window", "xnu-window", reference["xnu_window"]["start"],
             reference["xnu_window"]["bytes"], copy_phase, runtime, 0x4000),
    ]
    claims = [
        {**span("LK mb_kernel (source intent)", "reservation", 0x40000000, 0x7c80000,
                initial, initial), "kind": "buffer-claim", "buffer": "LK decompressed Image"},
        {**span("LK mb_dtb (source intent)", "reservation", 0x47c80000, 0x400000,
                initial, initial), "kind": "buffer-claim", "buffer": "Incoming FDT reservation"},
    ]
    claims += [{**span(row["name"], "reservation", row["start"], row["bytes"], initial, runtime),
                "kind": "excluded-reservation"} for row in mblock["reserved"]]
    profile = {"schema_version": 1, "name": "native-4m-var-historical-evidence",
               "buffers": buffers, "claims": claims,
               "scope": "historical-reservations-conservatively-retained; not a same-boot map"}
    lifetime_report = check_boot_lifetimes(memory_map, profile)
    alternatives = []
    for base in (0x1c0000000, 0x140000000, 0x200000000):
        candidate = copy.deepcopy(reference)
        delta = base - candidate["xnu_window"]["start"]
        candidate["name"] = "geometry-only-" + hex(base)
        candidate["xnu_window"]["start"] = base
        for region in candidate["regions"]:
            if region["role"] not in {"bootshim", "bootshim-stack", "embedded-payload", "image-padding"}:
                region["start"] += delta
        report = check_candidate(memory_map, candidate)
        # Linux dynamic requests remain potential conflicts in the old checker;
        # no claim is made that LK actually allocated those low ranges.
        report.update({"runtime_base": base, "baseline_offline_receipts_exist": base == 0x1c0000000,
                       "physical_boot_tested": False,
                       "current_native_preflight_base_matches": base == 0x1c0000000,
                       "new_candidate_created": False, "geometry": candidate["regions"]})
        alternatives.append(report)
    report = {"decision": "BLOCKED_BY_MEMORY_EVIDENCE", "inputs": receipt,
              "reference": reference, "mblock": mblock, "lk_binary": lk_evidence,
              "retained_log_scope": "Fastboot allocation trace, no actual XNU entry binding",
              "lifetime_profile": profile, "lifetime_result": lifetime_report,
              "alternatives": alternatives, "physical_execution_authorized": False,
              "phone_operations": [], "new_boot_images": [],
              "staging_input_output_known_lower_bound_bytes": reference["image"]["bytes"] +
                  reference["envelope"]["compressed_image_bytes"],
              "decompression_peak_proven": False}
    (args.output / "memory-ownership-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"decision": report["decision"], "mblock_free": len(mblock["free"]),
                      "mblock_reserved_matched": len(fixed), "lk_instruction_checks": len(expected),
                      "reference_historical_coverage": mblock["reference_extents"],
                      "phone_operations": []}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, struct.error) as error:
        sys.exit(str(error))
