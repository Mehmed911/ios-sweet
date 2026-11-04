#!/usr/bin/env python3
"""Build a fail-closed MT6897 UFS DMA-map receipt from pinned evidence.

This tool reads only the pinned Duchamp DTB and the pinned runtime/PRDT JSON
reports. It models Linux's ``bus_dma_region`` affine translation and validates
the separately approved v3 observation of the live range, raw DMA addresses
and SWIOTLB state.

The resulting direct-route receipt is evidence for address translation only.
It never enables the physical backend and does not claim firmware/firewall,
resource or cache-maintenance ownership. This tool itself performs no phone,
MMIO, SMC, DMA, UFS or partition access.
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
PRDT_V3_SHA256 = "0fc223d4474535f269766c268b74cab05b2028501ee234f3bab5eb1782053bc9"


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


def load_live_prdt_v3(repo, path):
    interpreter = repo / "tools/interpret-duchamp-prdt-v3-observation.py"
    spec = importlib.util.spec_from_file_location("duchamp_prdt_v3", interpreter)
    require(spec is not None and spec.loader is not None,
            "cannot load PRDT v3 interpreter")
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module.validate(path), interpreter


def build_report(repo, fdt_path, runtime_path, prdt_path, prdt_v3_path):
    fdt_raw = fdt_path.read_bytes()
    require(sha256(fdt_raw) == FDT_SHA256, "DTB hash differs")
    runtime = load_json(runtime_path, RUNTIME_SHA256, "runtime evidence")
    prdt = load_json(prdt_path, PRDT_SHA256, "PRDT interpretation")
    require(sha256(prdt_v3_path.read_bytes()) == PRDT_V3_SHA256,
            "PRDT v3 evidence hash differs")
    prdt_v3, prdt_v3_interpreter = load_live_prdt_v3(repo, prdt_v3_path)
    require(runtime.get("report_version") == 2 and
            runtime.get("audit_passed") is True,
            "runtime evidence did not pass")
    require(runtime.get("target") == {"device": "duchamp", "soc": "mt6897"},
            "runtime target differs")
    require(prdt.get("report_version") == 1 and
            prdt.get("verdict") == "validated-limited-prdt-evidence",
            "PRDT interpretation did not pass")
    require(prdt_v3.get("verdict") == "validated-live-direct-dma-evidence",
            "PRDT v3 live evidence did not pass")

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
    live = prdt_v3.get("proven", {})
    require(live.get("live_dma_range_entries_captured") is True and
            live.get("live_dma_range_is_identity") is True and
            live.get("raw_dma_equals_cpu_pa_for_all_observed_segments") is True and
            live.get(
                "forward_and_inverse_translation_for_all_observed_segments"
            ) is True,
            "live direct-DMA evidence is incomplete")
    require(live.get("dma_range_cpu_start") == windows[0]["cpu_start"] and
            live.get("dma_range_dma_start") == windows[0]["dma_start"] and
            live.get("dma_range_bytes") == windows[0]["bytes"],
            "live DMA range differs from the saved DT model")
    require(live.get("swiotlb_pool_inactive") is True and
            live.get("swiotlb_force_bounce_false") is True and
            live.get("no_swiotlb_segments_observed") is True,
            "live SWIOTLB disposition differs")

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
            "runtime_dma_range_entries_proven": True,
            "raw_dma_equals_cpu_pa_proven": True,
            "forward_and_inverse_translation_proven": True,
            "direct_route_receipt_issuable": True,
            "receipt_scope": "observed Linux UFS address route",
        },
        "bounce": {
            "disposition": "inactive-not-forced-no-bounce-observed",
            "swiotlb_pool_present": True,
            "swiotlb_pool_active": False,
            "swiotlb_force_bounce": False,
            "sample_no_swiotlb": True,
            "sample_segments": live["observed_segments_total"],
            "bounded_window_segments": live[
                "observed_segments_in_bounded_window"
            ],
            "observed_direct_route_proven": True,
            "global_bounce_disposition_proven": False,
            "bounce_route_receipt_issuable": False,
        },
        "blockers": [
            "physical firewall/firmware ownership is not proven",
            "XNU cache-maintenance ownership is not proven",
            "clock/reset/PHY/regulator ownership is not proven",
        ],
        "inputs": {
            "fdt": {"sha256": FDT_SHA256, "bytes": len(fdt_raw)},
            "runtime_evidence": {"sha256": RUNTIME_SHA256},
            "prdt_interpretation": {"sha256": PRDT_SHA256},
            "prdt_v3_live": {"sha256": PRDT_V3_SHA256},
            "prdt_v3_interpreter": str(
                prdt_v3_interpreter.relative_to(repo)
            ).replace("\\", "/"),
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
        "scope": (
            "validated live Linux UFS address route; physical backend remains "
            "disabled pending cache and firmware/resource ownership"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--runtime-evidence", type=Path, required=True)
    parser.add_argument("--prdt-evidence", type=Path, required=True)
    parser.add_argument("--prdt-v3-evidence", type=Path, required=True)
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
        args.prdt_v3_evidence.resolve(strict=True),
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(output, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({
        "passed": True,
        "output": str(output),
        "direct_route_receipt_issuable": report["candidate"][
            "direct_route_receipt_issuable"
        ],
        "bounce_disposition": report["bounce"]["disposition"],
        "physical_backend_enabled": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
