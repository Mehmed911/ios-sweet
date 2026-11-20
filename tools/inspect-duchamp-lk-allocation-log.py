#!/usr/bin/env python3
"""Extract observations from an existing OEM LK log; never grant hardware access.

This offline reader preserves slot, acquisition and producer limitations. It has
no phone transport and is not an input to the physical authorization gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


ALLOC = re.compile(
    r"mblock_alloc_range_no_lock:\d+: start: (0x[0-9a-f]+), sz: (0x[0-9a-f]+) "
    r"lower_bound: (0x[0-9a-f]+), limit: (0x[0-9a-f]+),"
    r"mblock_alloc_range_no_lock:\d+: map:(\d+) name:(\S+)", re.I)
FREE = re.compile(r"mblock_free_with_size:\d+: start (0x[0-9a-f]+) "
                  r"size: (0x[0-9a-f]+), name: (\S+)", re.I)
JUMP = re.compile(r"boot_linux_fdt:\d+: booting linux @ (0x[0-9a-f]+), "
                  r"ramdisk @ (0x[0-9a-f]+) \((\d+)\) dtb @ (0x[0-9a-f]+) \((\d+)\)", re.I)
TABLE = re.compile(r"LogTableHeader: magic=(0x[0-9a-f]+),\s+version=(0x[0-9a-f]+),\s+"
                   r"header_size=(0x[0-9a-f]+),\s+boot_index=([0-9a-f]+),\s+"
                   r"log_content_offset=(0x[0-9a-f]+)", re.I)
CONTENT = re.compile(r"LogContentHeader: magic=(0x[0-9a-f]+),\s+version=(0x[0-9a-f]+),\s+"
                     r"header_size=(0x[0-9a-f]+),\s+first_current_log_offset=([0-9a-f]+),\s+"
                     r"dump_count=(\d+),\s+dump_size=(0x[0-9a-f]+)", re.I)


def blackbox_messages(lines, producer_indices):
    """Check printed metadata only; this does not decode a historical record.

    The pinned writer at file+0x51d08..0x51d34 advances dump_count as a
    one-based cursor, wrapping 5 to 1. The banner is printed BEFORE advancing
    the persistent generation. No trusted origin or freshness is implied.
    """
    tables, contents = [], []
    for n, line in enumerate(lines, 1):
        t, c = TABLE.search(line), CONTENT.search(line)
        if t:
            values = [int(v, 16) for v in t.groups()]
            tables.append(dict(zip(("magic", "version", "header_size", "printed_generation",
                                    "content_header_offset"), values), line=n))
        if c:
            values = [int(v, 10 if i == 4 else 16) for i, v in enumerate(c.groups())]
            contents.append(dict(zip(("magic", "version", "header_size", "first_record_offset",
                                      "cursor_before_write", "record_stride"), values), line=n))
    problems = []
    if len(tables) != 1 or len(contents) != 1:
        problems.append("missing or ambiguous Blackbox metadata")
    else:
        t, c = tables[0], contents[0]
        if (t["magic"], t["version"], t["header_size"], t["content_header_offset"]) != (
                0x56775af41bcde0f0, 0x1000, 0x400, 0x800):
            problems.append("Blackbox table differs from audited format")
        if (c["magic"], c["version"], c["header_size"], c["first_record_offset"], c["record_stride"]) != (
                0xe99bb480dd25e1f0, 0x1000, 0x400, 0x1000, 0x800000):
            problems.append("Blackbox content differs from audited format")
        if not 0 <= c["cursor_before_write"] <= 5:
            problems.append("Blackbox ring cursor out of range")
        if len(producer_indices) != 2 or any(x["index"] != t["printed_generation"] for x in producer_indices):
            problems.append("Blackbox generation messages disagree")
        if t["printed_generation"] >= 1 << 32:
            problems.append("Blackbox generation exceeds firmware field")
    return {"printed_tables": tables, "printed_content_headers": contents,
            "ring_capacity_from_pinned_code": 5,
            "printed_generation_precedes_persistent_increment": True,
            "metadata_consistent": not problems, "issues": problems,
            "historical_export_supported": False, "historical_record_recovered": False,
            "record_freshness_established": False, "origin_authenticated": False}


def interval(start, size):
    if size <= 0 or start < 0 or start >= 1 << 64 or size > (1 << 64) - start:
        raise ValueError("invalid or overflowing logged interval")
    return {"start": start, "bytes": size, "end_exclusive": start + size}


def inspect(raw, capture):
    if not raw or len(raw) > 1024 * 1024:
        raise ValueError("empty or oversized LK log")
    lines = [s.rstrip("\r") for s in raw.decode(errors="replace").split("\n")]
    if max(map(len, lines)) > 16384:
        raise ValueError("oversized LK log line")
    allocations, releases, slots, jumps, decompress = [], [], [], [], []
    witnesses, producer_indices = [], []
    for n, line in enumerate(lines, 1):
        alloc, free, jump = ALLOC.search(line), FREE.search(line), JUMP.search(line)
        if alloc:
            a, z, lo, hi, mapping, name = alloc.groups()
            entry = interval(int(a, 16), int(z, 16))
            entry.update(line=n, lower_bound=int(lo, 16), limit=int(hi, 16),
                         mapping=int(mapping), name=name)
            allocations.append(entry)
        if free:
            a, z, name = free.groups()
            releases.append(dict(interval(int(a, 16), int(z, 16)), line=n, name=name))
        if jump:
            kernel, ramdisk, size, dtb, dtb_size = jump.groups()
            jumps.append({"line": n, "kernel": int(kernel, 16),
                          "ramdisk": interval(int(ramdisk, 16), int(size)),
                          "dtb": interval(int(dtb, 16), int(dtb_size))})
        match = re.search(r"Update version, boot successfully on slot ([01])\b", line)
        if match:
            slots.append({"line": n, "slot": "_a" if match[1] == "0" else "_b"})
        if "decompress_kernel takes" in line:
            decompress.append(n)
        index = re.search(r"LogTableHeader:.*\bboot_index=([0-9a-f]+),", line, re.I)
        if index:
            producer_indices.append({"line": n, "index": int(index[1], 16)})
        index = re.search(r"WritePLLKHardresetLog:.*\bboot_index = (\d+)\b", line)
        if index:
            producer_indices.append({"line": n, "index": int(index[1])})
        if any(t in line for t in ("mb_avb", "decompress_kernel takes", "booting linux @",
                                    "boot successfully on slot", "[CCCI]Trigger MD run",
                                    "clean_pgd done", "emi_mpu_set_protection ret=")):
            witnesses.append({"line": n, "text": line})
    pool = [a for a in allocations if a["name"] == "mb_avb"]
    freed = [a for a in releases if a["name"] == "mb_avb"]
    issues = []
    if len(pool) != 1 or len(freed) != 1 or len(jumps) != 1 or len(decompress) != 1:
        issues.append("missing or ambiguous allocation/release/decompression/jump events")
    else:
        a, f = pool[0], freed[0]
        if a["start"] != f["start"] or a["bytes"] != f["bytes"]:
            issues.append("release does not match allocation")
        if not a["line"] < decompress[0] < f["line"] < jumps[0]["line"]:
            issues.append("allocation lifetime event order is inconsistent")
        if a["bytes"] != 0x8c00000 or a["start"] & 4095:
            issues.append("pool differs from audited size/alignment")
        if a["lower_bound"] != 0 or a["limit"] != (1 << 64) - 1 or a["mapping"] != 0:
            issues.append("pool constraints differ from audited caller")
    commands = {r["name"]: r for r in capture.get("commands", [])}
    before, after = commands.get("boot_before", {}), commands.get("boot_after", {})
    log = commands.get("lk_log", {})
    acquired_slot = commands.get("slot", {}).get("text")
    stable_acquisition = (before.get("exit_code") == after.get("exit_code") == 0 and
                          bool(before.get("sha256")) and before.get("sha256") == after.get("sha256"))
    raw_matches = (log.get("exit_code") == 0 and log.get("bytes") == len(raw) and
                   log.get("sha256") == hashlib.sha256(raw).hexdigest())
    if not stable_acquisition:
        issues.append("Android boot changed or acquisition identity is missing")
    if not raw_matches:
        issues.append("raw bytes do not match acquisition receipt")
    slot_values = {row["slot"] for row in slots}
    consistent_slot = acquired_slot in ("_a", "_b") and slot_values == {acquired_slot}
    if not consistent_slot:
        issues.append("selected slot is missing, conflicting or differs from Android")
    blackbox = blackbox_messages(lines, producer_indices)
    issues.extend(blackbox["issues"])
    return {
        "schema": "duchamp-lk-allocation-observations-v1",
        "scope": "offline OEM log extraction; not authenticated firmware attestation",
        "raw_sha256": hashlib.sha256(raw).hexdigest(), "raw_bytes": len(raw),
        "slot_observed": acquired_slot, "slot_corroborated_in_log": consistent_slot,
        "stable_android_acquisition": stable_acquisition,
        "android_boot_id_digest": before.get("sha256"),
        "producer_boot_index_messages": producer_indices,
        "blackbox_printed_metadata": blackbox,
        "raw_matches_acquisition_receipt": raw_matches,
        "observation_consistent": not issues, "issues": issues,
        "mb_avb_allocations": pool, "mb_avb_release_messages": freed,
        "decompression_message_lines": decompress, "kernel_jump_messages": jumps,
        "allocations": allocations, "releases": releases, "witnesses": witnesses,
        "not_established": ["normal Slot B XNU boot identity", "vm_avb VA-to-PA mapping",
                            "loaded boot-data pointer and input extent", "release/unmap return status",
                            "final BL31 policy and reservation lifetime", "modem/peripheral DMA exclusion",
                            "IOMMU routing/domain/mapping epoch", "cache responsibility", "actual XNU entry"],
        "firmware_origin_authenticated": False,
        "complete_slot_b_handoff_established": False,
        "physical_access_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = inspect(args.log.read_bytes(), json.loads(args.capture.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("observation_consistent", "slot_observed",
                                            "mb_avb_allocations", "physical_access_authorized")}, indent=2))
    if not report["observation_consistent"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
