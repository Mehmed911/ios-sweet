#!/usr/bin/env python3
"""Check an offline Duchamp placement map without granting hardware access."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


U64_MAX = (1 << 64) - 1


@dataclass(frozen=True)
class Interval:
    start: int
    end: int

    @classmethod
    def from_row(cls, row):
        start, size = row["start"], row["bytes"]
        if (type(start) is not int or type(size) is not int or
                start < 0 or start > U64_MAX or not 0 < size <= U64_MAX - start):
            raise ValueError(f"invalid uint64 interval for {row.get('name', '<unnamed>')}")
        return cls(start, start + size)

    def intersects(self, other):
        return self.start < other.end and other.start < self.end

    def contains(self, other):
        return self.start <= other.start and other.end <= self.end


def coverage_by_banks(interval, banks):
    cursor = interval.start
    for bank in banks:
        if bank.start > cursor:
            return False
        cursor = max(cursor, bank.end)
        if cursor >= interval.end:
            return True
    return False


def checked_range(row):
    interval = Interval.from_row(row)
    alignment = row["alignment"]
    if (type(alignment) is not int or not 0 < alignment <= U64_MAX or
            alignment & (alignment - 1) or interval.start % alignment):
        raise ValueError(f"invalid start alignment for {row['name']}")
    length_alignment = row["length_alignment"]
    if (type(length_alignment) is not int or not 0 < length_alignment <= U64_MAX or
            length_alignment & (length_alignment - 1) or row["bytes"] % length_alignment):
        raise ValueError(f"invalid length alignment for {row['name']}")
    return interval


def check_candidate(memory_map, candidate):
    version = memory_map["schema_version"]
    if type(version) is not int or version != 1:
        raise ValueError("unsupported memory map version")
    banks = sorted((Interval.from_row(row) for row in memory_map["ram_banks"]),
                   key=lambda interval: interval.start)
    fixed = [(row["name"], Interval.from_row(row)) for row in memory_map["fixed_reservations"]]
    dynamic = [(row["name"], [Interval.from_row(bound) for bound in row["allocation_ranges"]])
               for row in memory_map["dynamic_requests"]]
    window_row = candidate["xnu_window"]
    if window_row["role"] != "xnu-window":
        raise ValueError("missing XNU runtime window")
    window = checked_range(window_row)
    spans = [(row, checked_range(row)) for row in candidate["regions"]]
    problems = []

    def flag(region, problem, other=None):
        entry = {"region": region, "problem": problem}
        if other is not None:
            entry["other"] = other
        problems.append(entry)

    required = ("bootshim", "bootshim-stack", "embedded-payload", "xnu-segment",
                "md0", "md1", "adt", "boot-args", "xnu-allocator")
    staging_roles = {"bootshim", "bootshim-stack", "embedded-payload", "image-padding"}
    known_roles = set(required) | staging_roles
    roles = {row["role"] for row, _ in spans}
    for role in required:
        if role not in roles:
            flag(role, "missing-required-region")
    for row, _ in spans:
        if row["role"] not in known_roles:
            flag(row["name"], "unknown-region-role")
    for row, interval in spans + [(window_row, window)]:
        name = row["name"]
        if not coverage_by_banks(interval, banks):
            flag(name, "outside-declared-ram")
        if row is not window_row:
            if row["role"] in staging_roles:
                if interval.intersects(window):
                    flag(name, "staging-intersects-xnu-window")
            elif not window.contains(interval):
                flag(name, "destination-outside-xnu-window")
        for reserved_name, reserved in fixed:
            if interval.intersects(reserved):
                flag(name, "intersects-fixed-reservation", reserved_name)
        for request_name, possible in dynamic:
            if not possible or any(interval.intersects(bound) for bound in possible):
                flag(name, "intersects-unresolved-dynamic-reservation", request_name)

    ordered = sorted(spans, key=lambda item: (item[1].start, item[1].end))
    for index, (row, interval) in enumerate(ordered):
        for other_row, other in ordered[index + 1:]:
            if other.start >= interval.end:
                break
            flag(row["name"], "overlaps-candidate-region", other_row["name"])

    # A disk file or a successful geometry check cannot establish the final
    # firmware allocator state, a resource grant, or DMA isolation.
    evidence_missing = [
        "same-boot-lk-and-bl31-final-memory-map",
        "independently-verified-ownership-of-staging-and-xnu-window",
        "same-boot-dma-isolation-for-staging-and-xnu-window",
    ]
    return {
        "candidate": candidate["name"],
        "structural_findings": problems,
        "missing_physical_evidence": evidence_missing,
        "decision": "BLOCKED_BY_MEMORY_EVIDENCE",
        "physical_execution_authorized": False,
    }


BOOT_PHASES = ("lk-decompress", "lk-finalize", "bl31-exit",
               "bootshim-materialize", "xnu-runtime")


def check_boot_lifetimes(memory_map, profile):
    """Check declared buffer lifetimes against archived/source reservation intent.

    This is an additional offline geometry audit, not an authorization format.
    In particular a matching claim does not prove it survived to this boot, and
    a free pool says nothing about a modem, IOMMU, MPU, or outstanding DMA.
    """
    if type(profile.get("schema_version")) is not int or profile["schema_version"] != 1:
        raise ValueError("unsupported lifetime profile")
    if type(memory_map.get("schema_version")) is not int or memory_map["schema_version"] != 1:
        raise ValueError("unsupported memory map version")
    banks = sorted((Interval.from_row(row) for row in memory_map["ram_banks"]),
                   key=lambda item: item.start)
    buffers, claims = profile["buffers"], profile["claims"]
    findings, parsed, names = [], [], set()

    def flag(name, problem, other=None):
        finding = {"region": name, "problem": problem}
        if other is not None:
            finding["other"] = other
        findings.append(finding)

    def lifetime(row):
        try:
            first = BOOT_PHASES.index(row["first_phase"])
            last = BOOT_PHASES.index(row["last_phase"])
        except (KeyError, ValueError) as error:
            raise ValueError("unknown reservation/buffer lifetime") from error
        if last < first:
            raise ValueError("reversed reservation/buffer lifetime")
        return first, last

    for row in buffers:
        name = row["name"]
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("duplicate or invalid buffer name")
        names.add(name)
        first, last = lifetime(row)
        interval = None
        if row.get("start") is None or row.get("bytes") is None:
            flag(name, "unknown-buffer-extent")
        else:
            interval = checked_range(row)
            if not coverage_by_banks(interval, banks):
                flag(name, "outside-declared-ram")
        # This audit accepts geometry, never a caller-supplied DMA grant.
        flag(name, "unknown-dma-ownership")
        parsed.append((row, interval, first, last))

    required = {"compressed-input", "decompression-scratch", "lk-output",
                "fdt", "xnu-window"}
    for role in sorted(required - {row["role"] for row in buffers}):
        flag(role, "missing-required-lifetime-buffer")
    parsed_claims = []
    for row in claims:
        if row["kind"] not in ("buffer-claim", "excluded-reservation"):
            raise ValueError("unknown reservation kind")
        if row["kind"] == "buffer-claim" and row["buffer"] not in names:
            raise ValueError("claim references unknown buffer")
        first, last = lifetime(row)
        parsed_claims.append((row, checked_range(row), first, last))
    for row, interval, first, last in parsed:
        if interval is None:
            continue
        for other, reserved, a, b in parsed_claims:
            if (other["kind"] == "excluded-reservation" and
                    max(first, a) <= min(last, b) and interval.intersects(reserved)):
                flag(row["name"], "overlaps-active-reservation", other["name"])
        for phase in range(first, last + 1):
            if not any(claim["kind"] == "buffer-claim" and
                       claim["buffer"] == row["name"] and
                       a <= phase <= b and extent.contains(interval)
                       for claim, extent, a, b in parsed_claims):
                flag(row["name"], "missing-claim-during-phase", BOOT_PHASES[phase])
    for index, (row, interval, first, last) in enumerate(parsed):
        if interval is None:
            continue
        for other, extent, a, b in parsed[index + 1:]:
            if (extent is not None and max(first, a) <= min(last, b) and
                    interval.intersects(extent)):
                flag(row["name"], "overlaps-live-buffer", other["name"])
    return {"name": profile["name"], "findings": findings,
            "decision": "BLOCKED_BY_MEMORY_EVIDENCE",
            "physical_execution_authorized": False,
            "scope": "offline-lifetime-geometry-only",
            "missing_physical_evidence": [
                "actual-same-boot-reservation-lifetimes",
                "independently-established-memory-ownership",
                "same-boot-dma-exclusion-and-firmware-writers"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", type=Path)
    args = parser.parse_args()
    try:
        memory_map = json.loads(args.map.read_text(encoding="utf-8"))
        candidates = memory_map["candidates"]
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("at least one candidate is required")
        results = [check_candidate(memory_map, candidate) for candidate in candidates]
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"invalid placement map: {error}", file=sys.stderr)
        return 2
    print(json.dumps(results, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())
