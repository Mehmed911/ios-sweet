#!/usr/bin/env python3
"""Inspect the saved Duchamp tee_a image without accessing the phone.

The command pins the exact read-only capture, validates the first packaged
``atf`` entry and records the BL31 identity strings that are also present in
the bounded runtime ATF log.  It deliberately makes no source-equivalence,
SMC-effect, ownership or UFS-readiness claim.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


EXPECTED_BYTES = 5 * 1024 * 1024
EXPECTED_SHA256 = "37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d"
OUTER_MAGIC = 0x58881688
INNER_MAGIC = 0x58891689
EXPECTED_ENTRY_NAME = "atf"
EXPECTED_NEXT_ENTRY_NAME = "cert1"
EXPECTED_HEADER_BYTES = 0x200
EXPECTED_DECLARED_PAYLOAD_BYTES = 0xE8E78
ALIGNMENT = 0x10

BL31_RELEASE = "lts-v2.8.6(release):2fbca47"
BL31_BUILT = "Built : 07:19:18, Dec 18 2024"
BL31_SOFTWARE = "common_2.6.1"
BL31_PLATFORM = "6897-1.2"
BL31_SOFTWARE_BUILT = "Jun 8 2022"
BL31_SOFTWARE_BUILD_HOST_TIME = "Jul 25 20:00:00 UTC 2023"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def u32(raw, offset):
    require(offset >= 0 and offset + 4 <= len(raw), "truncated 32-bit field")
    return struct.unpack_from("<I", raw, offset)[0]


def c_string(raw, offset, width):
    require(offset >= 0 and width > 0 and offset + width <= len(raw),
            "truncated string field")
    field = raw[offset:offset + width]
    value = field.split(b"\0", 1)[0]
    try:
        return value.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("non-ASCII string field") from error


def align_up(value, alignment):
    require(alignment > 0 and alignment & (alignment - 1) == 0,
            "alignment must be a power of two")
    return (value + alignment - 1) & ~(alignment - 1)


def unique_offset(raw, needle, start, end, label):
    encoded = needle.encode("ascii")
    first = raw.find(encoded, start, end)
    require(first >= 0, f"missing BL31 identity string: {label}")
    second = raw.find(encoded, first + 1, end)
    require(second < 0, f"duplicate BL31 identity string: {label}")
    return first


def inspect_image(raw, expected_bytes=None, expected_sha256=None):
    """Return a strict local-file report for a tee image byte string."""
    receipt = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    if expected_bytes is not None:
        require(receipt["bytes"] == expected_bytes, "tee_a size differs")
    if expected_sha256 is not None:
        require(receipt["sha256"] == expected_sha256, "tee_a SHA-256 differs")

    require(len(raw) >= EXPECTED_HEADER_BYTES, "truncated tee package header")
    require(u32(raw, 0) == OUTER_MAGIC, "unexpected first-entry outer magic")
    declared_bytes = u32(raw, 4)
    require(declared_bytes == EXPECTED_DECLARED_PAYLOAD_BYTES,
            "unexpected atf declared payload size")
    require(c_string(raw, 8, 32) == EXPECTED_ENTRY_NAME,
            "unexpected first-entry name")
    require(u32(raw, 0x30) == INNER_MAGIC,
            "unexpected first-entry inner magic")
    payload_offset = u32(raw, 0x34)
    require(payload_offset == EXPECTED_HEADER_BYTES,
            "unexpected atf payload offset")

    payload_start = payload_offset
    payload_end = payload_start + declared_bytes
    require(payload_end <= len(raw), "atf declared payload exceeds image")
    next_entry_offset = align_up(payload_end, ALIGNMENT)
    require(next_entry_offset + EXPECTED_HEADER_BYTES <= len(raw),
            "next package entry is truncated")
    padding = raw[payload_end:next_entry_offset]
    require(all(byte == 0 for byte in padding),
            "non-zero bytes in atf alignment padding")
    require(u32(raw, next_entry_offset) == OUTER_MAGIC,
            "next package entry does not begin at aligned atf end")
    next_name = c_string(raw, next_entry_offset + 8, 32)
    require(next_name == EXPECTED_NEXT_ENTRY_NAME,
            "unexpected entry after atf")
    require(u32(raw, next_entry_offset + 0x30) == INNER_MAGIC,
            "unexpected next-entry inner magic")

    identities = {
        "release": BL31_RELEASE,
        "built": BL31_BUILT,
        "software": BL31_SOFTWARE,
        "platform": BL31_PLATFORM,
        "software_built": BL31_SOFTWARE_BUILT,
        "software_build_host_time": BL31_SOFTWARE_BUILD_HOST_TIME,
    }
    offsets = {
        key: unique_offset(raw, text, payload_start, payload_end, key)
        for key, text in identities.items()
    }
    runtime_identity = {
        "release": BL31_RELEASE,
        "built": BL31_BUILT.removeprefix("Built : "),
        "software_version": f"{BL31_SOFTWARE}({BL31_PLATFORM})",
        "software_build": (
            f"{BL31_SOFTWARE_BUILT}({BL31_SOFTWARE_BUILD_HOST_TIME})"
        ),
    }

    return {
        "report_version": 1,
        "passed": True,
        "input": receipt,
        "atf_entry": {
            "outer_magic": f"0x{OUTER_MAGIC:08x}",
            "inner_magic": f"0x{INNER_MAGIC:08x}",
            "name": EXPECTED_ENTRY_NAME,
            "declared_payload_bytes": declared_bytes,
            "header_payload_offset": payload_offset,
            "payload_start": payload_start,
            "payload_end_exclusive": payload_end,
            "alignment_bytes": ALIGNMENT,
            "alignment_padding_bytes": len(padding),
            "next_entry_offset": next_entry_offset,
            "next_entry_name": next_name,
        },
        "bl31_binary_identity": {
            "status": "observed-in-atf-entry",
            **runtime_identity,
            "string_offsets": offsets,
            "matches_bounded_runtime_log_identity": True,
        },
        "claims": {
            "captured_tee_a_binary_identity_verified": True,
            "bl31_runtime_identity_string_match_verified": True,
            "bl31_public_source_equivalence_verified": False,
            "bl31_ufs_sip_effect_contract_verified": False,
            "physical_resource_ownership_verified": False,
            "xnu_physical_ufs_ready": False,
        },
        "safety": {
            "local_file_only": True,
            "adb_access_by_this_tool": False,
            "phone_write": False,
            "partition_write": False,
            "fastboot_access": False,
            "mmio_access": False,
            "smc_execution": False,
        },
        "scope": (
            "local captured-binary structure and identity only; not source "
            "equivalence, SMC behavior, resource ownership or phone readiness"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing output")
    try:
        raw = args.image.resolve().read_bytes()
        report = inspect_image(raw, EXPECTED_BYTES, EXPECTED_SHA256)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n",
                               encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.exit(1, "tee inspection failed: " + str(error) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
