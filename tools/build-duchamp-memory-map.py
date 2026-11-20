#!/usr/bin/env python3
"""Combine archived FDT evidence and offline native preflights into a placement map."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

from duchamp_memory_placement import check_candidate
from duchamp_xnu_link import verify


PAGE = 0x4000


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def region(name, role, start, end, alignment, length_alignment, expected_owner):
    return {
        "name": name, "role": role, "start": start, "bytes": end - start,
        "alignment": alignment, "length_alignment": length_alignment,
        "expected_owner": expected_owner, "same_boot_ownership": "unverified",
    }


def read_symbols(listing):
    symbols = {}
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    return symbols


def read_candidate(directory, saved_fdt_hash, kernel_hash, segment_names, kernel_symbols):
    proof_path = directory / "verification.json"
    proof = read_json(proof_path)
    if (proof["kernel_sha256"] != kernel_hash or proof["saved_fdt_sha256"] != saved_fdt_hash or
            proof["physical_boot_tested"] or proof["physical_ufs_enabled"] or
            not proof["bootshim_preflight_passed"] or not proof["materialization_passed"] or
            proof["pack"]["exit_code"] != 0):
        raise ValueError(f"inconsistent preflight receipt in {directory}")
    image_path = directory / "bootshim" / "Image"
    envelope_path = directory / "boot-v4-envelope.img"
    image, plan, pack = proof["image"], proof["plan"], proof["pack"]
    if (image_path.stat().st_size != image["bytes"] or sha256(image_path) != image["sha256"] or
            envelope_path.stat().st_size != pack["bytes"] or sha256(envelope_path) != pack["sha256"]):
        raise ValueError(f"image differs from receipt in {directory}")
    symbols = read_symbols((directory / "bootshim-symbols.log").read_text(encoding="utf-8"))
    base = image["load_pa"]
    offsets = [symbols[name] for name in ("_head", "_bss_end", "_stack_top",
                                         "duchamp_embedded_payload_start",
                                         "duchamp_embedded_payload_end", "_end")]
    head, stack_bottom, stack_top, payload_start, payload_end, end = offsets
    if (offsets != sorted(offsets) or head != 0 or end != image["bytes"] or
            base + end != image["end_pa"] or payload_end - payload_start != plan["payload_bytes"]):
        raise ValueError(f"Image symbols disagree with the packaged extents in {directory}")
    parts = [
        ("bootshim-code-data-bss", "bootshim", head, stack_bottom),
        ("bootshim-stack", "bootshim-stack", stack_bottom, stack_top),
        ("pre-payload-padding", "image-padding", stack_top, payload_start),
        ("embedded-payload", "embedded-payload", payload_start, payload_end),
        ("image-tail-padding", "image-padding", payload_end, end),
    ]
    spans = [region(name, role, base + start, base + finish,
                    16 if role != "image-padding" else 1, 1, "LK staging then Bootshim")
             for name, role, start, finish in parts if start < finish]
    volumes = {plan["volumes"][name]["pa"]: label for name, label in (("root", "md0"), ("var", "md1"))}
    for item in plan["segments"]:
        role = volumes.get(item["pa"], "xnu-segment")
        name = role if role in ("md0", "md1") else segment_names[item["va"]]
        spans.append(region(name, role, item["pa"], item["pa"] + item["vmsize"], PAGE, PAGE, "XNU"))
    phys_base = plan["physical_base"]
    window_end = phys_base + plan["window_bytes"]
    spans.extend([
        region("ADT and padding", "adt", plan["adt_pa"], plan["boot_args_pa"], PAGE, PAGE, "XNU"),
        region("boot-args page", "boot-args", plan["boot_args_pa"], plan["reserved_end"],
               PAGE, PAGE, "XNU"),
        region("early page tables, allocator and VM", "xnu-allocator", plan["reserved_end"],
               window_end, PAGE, PAGE, "XNU"),
    ])
    symbol_locations = {}
    for name in ("_bootstrap_pagetables", "_intstack", "_excepstack"):
        address = phys_base + kernel_symbols[name] - plan["virtual_base"]
        containing = next(item["name"] for item in spans if item["role"] == "xnu-segment"
                          and item["start"] <= address < item["start"] + item["bytes"])
        symbol_locations[name] = {"pa": address, "contained_in": containing}
    return {
        "name": directory.name,
        "source_receipt": str(proof_path.resolve()),
        "source_receipt_sha256": sha256(proof_path),
        "image": image,
        "envelope": pack,
        "xnu_window": region("XNU runtime window", "xnu-window", phys_base, window_end,
                             PAGE, PAGE, "XNU"),
        "regions": spans,
        "kernel_symbol_locations": symbol_locations,
        "volumes": plan["volumes"],
        "known_materialized_prefix_bytes": plan["reserved_end"] - phys_base,
        "xnu_runtime_allocator_capacity_bytes": window_end - plan["reserved_end"],
        "outer_lz4_simultaneous_input_output_bytes_excluding_scratch":
            image["bytes"] + pack["compressed_image_bytes"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("candidates", type=Path, nargs="+")
    args = parser.parse_args()
    archive = read_json(args.archive)
    fdt_hash, kernel_hash = sha256(args.fdt), sha256(args.kernel)
    if archive["fdt_sha256"] != fdt_hash:
        raise ValueError("saved FDT differs from the archived audit")
    fdt = args.fdt.read_bytes()
    magic, fdt_bytes, structure_offset, _, reserve_offset = struct.unpack_from(">5I", fdt)
    if magic != 0xd00dfeed or not 40 <= reserve_offset <= structure_offset <= fdt_bytes <= len(fdt):
        raise ValueError("invalid FDT reserve map bounds")
    fixed = [{**item, "source_scope": "archived Android FDT"}
             for item in archive["fixed_reservations"]]
    for offset in range(reserve_offset, structure_offset - 15, 16):
        address, size = struct.unpack_from(">2Q", fdt, offset)
        if not address and not size:
            break
        fixed.append(dict(name=f"FDT reserve map entry {offset:#x}", start=address, bytes=size,
                          source_scope="archived Android FDT"))
    else:
        raise ValueError("FDT memory reserve map has no terminator")
    for item in archive["additional_exclusions"]:
        fixed.append({**item, "bytes": item["end_exclusive"] - item["start"],
                      "source_scope": "archived Android FDT and historical handoff"})
    macho = verify(args.kernel.read_bytes())
    segment_names = {item["vmaddr"]: item["name"] for item in macho["segments"] if item["vmsize"]}
    kernel_symbols = read_symbols(subprocess.run(
        ["llvm-nm", str(args.kernel)], capture_output=True, text=True, check=True).stdout)
    memory_map = {
        "schema_version": 1,
        "scope": "offline geometry using archived Android FDT and modeled XNU destinations",
        "archives": {
            "fdt": str(args.fdt.resolve()), "fdt_sha256": fdt_hash,
            "kernel": str(args.kernel.resolve()), "kernel_sha256": kernel_hash,
            "memory_audit": str(args.archive.resolve()), "memory_audit_sha256": sha256(args.archive),
        },
        "ram_banks": archive["memory_banks"],
        "fixed_reservations": fixed,
        "dynamic_requests": [{**item, "actual_allocation": "unverified for Slot B"}
                             for item in archive["dynamic_reservations"]],
        "dma_sensitive_ranges": [
            {"region": "LK staging", "isolation": "unknown",
             "scope": "final firmware decompression through Bootshim materialization"},
            {"region": "XNU runtime window", "isolation": "unknown",
             "scope": "all pages including allocator, page tables and RAM disks"},
        ],
        "candidates": [read_candidate(item, fdt_hash, kernel_hash, segment_names, kernel_symbols)
                       for item in args.candidates],
    }
    memory_map["decisions"] = [check_candidate(memory_map, item) for item in memory_map["candidates"]]
    args.output.write_text(json.dumps(memory_map, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
