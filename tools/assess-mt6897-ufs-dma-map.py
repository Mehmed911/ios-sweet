#!/usr/bin/env python3
"""Build a fail-closed MT6897 UFS DMA-map candidate from saved evidence.

This tool reads only the pinned Duchamp DTB and the pinned runtime/PRDT JSON
reports.  It models Linux's ``bus_dma_region`` affine translation, but it does
not promote a Device Tree declaration into a live PA-to-DMA proof.  In
particular, a present SWIOTLB pool and a no-bounce read sample leave the global
bounce disposition UNKNOWN.

The report is therefore suitable for offline review and boundary tests only.
It cannot issue an XNU DMA-route receipt and performs no phone, MMIO, SMC, DMA,
UFS or partition access.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


REPORT_VERSION = 1
U64_MAX = (1 << 64) - 1
FDT_SHA256 = "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29"
RUNTIME_SHA256 = "71236c08c0354ff0733d44a64e505d117dfd4594e370bedd81fad3ec93d1bf4d"
PRDT_SHA256 = "1e4c735d316004c83f9db71538186357112c7567daecd12be52ba24e74ea4018"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_end(start, size, label):
    require(isinstance(start, int) and isinstance(size, int),
            label + " must use integers")
    require(0 <= start <= U64_MAX, label + " start is outside uint64")
    require(size > 0, label + " size must be non-zero")
    require(size <= U64_MAX - start + 1, label + " overflows uint64")
    return start + size


def decode_dma_ranges(node):
    """Decode DT dma-ranges as Linux bus_dma_region candidates."""
    require(node.parent is not None, node.path + " has no parent address space")
    child_cells = node.scalar("#address-cells", 2)
    parent_cells = node.parent.scalar("#address-cells", 2)
    size_cells = node.scalar("#size-cells", 1)
    width = child_cells + parent_cells + size_cells
    require(1 <= child_cells <= 2 and 1 <= parent_cells <= 2 and
            1 <= size_cells <= 2, node.path + " uses unsupported cell widths")
    cells = node.cells("dma-ranges")
    require(cells and len(cells) % width == 0,
            node.path + " has malformed dma-ranges")
    windows = []
    for index in range(0, len(cells), width):
        dma_start = 0
        for cell in cells[index:index + child_cells]:
            dma_start = (dma_start << 32) | cell
        cpu_index = index + child_cells
        cpu_start = 0
        for cell in cells[cpu_index:cpu_index + parent_cells]:
            cpu_start = (cpu_start << 32) | cell
        size_index = cpu_index + parent_cells
        size = 0
        for cell in cells[size_index:size_index + size_cells]:
            size = (size << 32) | cell
        checked_end(cpu_start, size, "cpu window")
        checked_end(dma_start, size, "dma window")
        windows.append({
            "cpu_start": cpu_start,
            "dma_start": dma_start,
            "bytes": size,
            "offset": cpu_start - dma_start,
            "identity": cpu_start == dma_start,
        })
    return windows


def translate_pa_to_dma(windows, physical_address, size):
    end = checked_end(physical_address, size, "physical request")
    matches = []
    for window in windows:
        window_end = checked_end(window["cpu_start"], window["bytes"],
                                 "cpu window")
        if window["cpu_start"] <= physical_address and end <= window_end:
            dma_address = physical_address - window["offset"]
            checked_end(dma_address, size, "DMA request")
            matches.append(dma_address)
    require(len(matches) == 1, "physical request is unmapped or ambiguous")
    return matches[0]


def translate_dma_to_pa(windows, dma_address, size):
    end = checked_end(dma_address, size, "DMA request")
    matches = []
    for window in windows:
        window_end = checked_end(window["dma_start"], window["bytes"],
                                 "dma window")
        if window["dma_start"] <= dma_address and end <= window_end:
            physical_address = dma_address + window["offset"]
            checked_end(physical_address, size, "physical request")
            matches.append(physical_address)
    require(len(matches) == 1, "DMA request is unmapped or ambiguous")
    return matches[0]


def load_json(path, expected_sha256, label):
    raw = path.read_bytes()
    require(sha256(raw) == expected_sha256, label + " hash differs")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(label + " is not valid UTF-8 JSON") from error
    require(isinstance(value, dict), label + " is not a JSON object")
    return value


def load_fdt(repo, raw):
    parser = repo / "tools/inspect-duchamp-hardware.py"
    spec = importlib.util.spec_from_file_location("duchamp_dma_map_fdt", parser)
    require(spec is not None and spec.loader is not None,
            "cannot load bounded FDT parser")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module.Fdt(raw), parser


def build_report(repo, fdt_path, runtime_path, prdt_path):
    fdt_raw = fdt_path.read_bytes()
    require(sha256(fdt_raw) == FDT_SHA256, "DTB hash differs")
    runtime = load_json(runtime_path, RUNTIME_SHA256, "runtime evidence")
    prdt = load_json(prdt_path, PRDT_SHA256, "PRDT interpretation")
    require(runtime.get("report_version") == 2 and
            runtime.get("audit_passed") is True,
            "runtime evidence did not pass")
    require(runtime.get("target") == {"device": "duchamp", "soc": "mt6897"},
            "runtime target differs")
    require(prdt.get("report_version") == 1 and
            prdt.get("verdict") == "validated-limited-prdt-evidence",
            "PRDT interpretation did not pass")

    tree, parser_path = load_fdt(repo, fdt_raw)
    root = tree.nodes.get("/")
    require(root is not None and "mediatek,MT6897" in root.strings("compatible"),
            "DTB is not the pinned MT6897 tree")
    soc = tree.nodes.get("/soc")
    require(soc is not None and "dma-ranges" in soc.props,
            "saved DTB has no /soc dma-ranges")
    windows = decode_dma_ranges(soc)
    require(len(windows) == 1, "expected one saved /soc DMA window")

    iommu = runtime.get("iommu_route", {})
    masks = runtime.get("dma_masks", {})
    proven = prdt.get("proven", {})
    not_proven = prdt.get("not_proven", {})
    require(iommu.get("linux_dma_api_path") == "generic dma-direct",
            "saved Linux route was not generic dma-direct")
    require(iommu.get("device_swiotlb_pool_present") is True,
            "saved runtime evidence did not expose a SWIOTLB pool")
    require(proven.get("no_swiotlb_observed_in_sample") is True,
            "saved PRDT sample did not prove no observed SWIOTLB segments")
    require(not_proven.get("raw_dma_address_equals_cpu_physical") is False,
            "PRDT report unexpectedly claims raw PA-to-DMA identity")

    boundary_vectors = []
    window = windows[0]
    candidates = [
        (window["cpu_start"], 1),
        (window["cpu_start"] + min(window["bytes"] - 1, 0xffffffff), 1),
        (window["cpu_start"] + window["bytes"] - 1, 1),
    ]
    bus_limit = int(masks.get("bus_dma_limit", "0"), 0)
    if window["cpu_start"] <= bus_limit < window["cpu_start"] + window["bytes"]:
        candidates.append((bus_limit, 1))
    for physical_address, size in candidates:
        dma_address = translate_pa_to_dma(windows, physical_address, size)
        require(translate_dma_to_pa(windows, dma_address, size) == physical_address,
                "DMA-map round trip differs")
        boundary_vectors.append({
            "physical_address": hex(physical_address),
            "dma_address": hex(dma_address),
            "bytes": size,
        })

    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "target": {"device": "duchamp", "soc": "mt6897", "engine": "ufs"},
        "candidate": {
            "source": "saved /soc dma-ranges",
            "windows": [{
                "cpu_start": hex(item["cpu_start"]),
                "dma_start": hex(item["dma_start"]),
                "bytes": hex(item["bytes"]),
                "offset": item["offset"],
                "identity": item["identity"],
            } for item in windows],
            "boundary_vectors": boundary_vectors,
            "static_dt_translation_model_proven": True,
            "runtime_dma_range_entries_proven": False,
            "raw_dma_equals_cpu_pa_proven": False,
            "direct_route_receipt_issuable": False,
        },
        "bounce": {
            "disposition": "unknown",
            "swiotlb_pool_present": True,
            "sample_no_swiotlb": True,
            "sample_segments": prdt["observation"]["segments_delta"],
            "global_bounce_disposition_proven": False,
            "bounce_route_receipt_issuable": False,
        },
        "blockers": [
            "live dma_range_map entries are not captured",
            "raw DMA addresses were not paired with CPU physical addresses",
            "SWIOTLB force state and global bounce disposition are unknown",
            "physical firewall/firmware ownership is not proven",
        ],
        "inputs": {
            "fdt": {"sha256": FDT_SHA256, "bytes": len(fdt_raw)},
            "runtime_evidence": {"sha256": RUNTIME_SHA256},
            "prdt_interpretation": {"sha256": PRDT_SHA256},
            "bounded_parser": str(parser_path.relative_to(repo)).replace("\\", "/"),
        },
        "safety": {
            "local_files_only": True,
            "phone_access": False,
            "mmio_access": False,
            "smc_execution": False,
            "dma_or_ufs_commands": False,
            "partition_access": False,
            "physical_backend_enabled": False,
        },
        "scope": "offline candidate only; not a live PA-to-DMA or bounce proof",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--prdt-evidence", type=Path, required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(
        repo,
        args.fdt.resolve(strict=True),
        args.runtime_evidence.resolve(strict=True),
        args.prdt_evidence.resolve(strict=True),
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(output, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "passed": True,
        "output": str(output),
        "bounce_disposition": report["bounce"]["disposition"],
        "physical_backend_enabled": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
