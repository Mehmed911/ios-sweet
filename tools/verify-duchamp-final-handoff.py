#!/usr/bin/env python3
"""Correlate independently authenticated final-exit and XNU-entry observations offline."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import time


BOARD = "duchamp/mt6897"
PHYSICAL_SCOPE = "duchamp-physical-slot-b"
FORMAT = "duchamp-final-handoff-v1"
SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")
IMAGES = ("lk", "bl31", "boot_b", "vendor_boot_b", "init_boot_b", "xnu_payload")
SOURCES = {
    "queues": "lk-ufs-owner",
    "reset": "bl31-reset-owner",
    "clocks_power_phy": "clock-power-phy-owners",
    "resource_access": "platform-resource-authority",
    "dma_drain_isolation": "dma-fabric-authority",
    "iommu_route": "dma-routing-authority",
    "cache": "system-cache-authority",
}
COMMON = {
    "format", "scope", "board", "device", "challenge", "boot_id", "slot",
    "stage", "sequence", "images", "fdt_sha256",
}


class Rejected(ValueError):
    """A malformed, untrusted or incompatible capture."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bounded(path, limit):
    require(path.is_file() and not path.is_symlink(), f"{path.name}: expected a regular file")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(0 < len(data) <= limit, f"{path.name}: invalid input length")
    return data


def unique_object(pairs):
    data = {}
    for key, value in pairs:
        require(key not in data, f"duplicate JSON key: {key}")
        data[key] = value
    return data


def load_json(raw):
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except Rejected:
        raise
    except (ValueError, RecursionError) as error:
        raise Rejected("invalid capture JSON") from error
    require(type(value) is dict, "expected a JSON object")
    return value


def fields(value, expected, name):
    require(type(value) is dict and set(value) == set(expected), f"{name}: unexpected or missing fields")


def hex_value(value, digits, name):
    require(isinstance(value, str) and len(value) == digits and
            re.fullmatch("[0-9a-f]+", value) and int(value, 16) != 0, f"{name}: invalid hex value")
    return value


def unsigned(value, name, minimum=1, maximum=(1 << 64) - 1):
    require(type(value) is int and minimum <= value <= maximum, f"{name}: invalid integer")
    return value


def verify_signature(public_key, pin, record, signature):
    require(len(public_key) == len(SPKI_PREFIX) + 32 and public_key.startswith(SPKI_PREFIX),
            "expected a DER Ed25519 public key")
    require(digest(public_key) == pin, "public key does not match out-of-band pin")
    require(len(signature) == 64, "invalid Ed25519 signature length")
    # Verify the exact bytes that will be parsed. Take an immutable private
    # copy so replacements of the input files cannot change those bytes.
    with tempfile.TemporaryDirectory(prefix="duchamp-handoff-") as temp:
        key, message, sig = (Path(temp) / name for name in ("key.der", "record.json", "signature"))
        for path, value in ((key, public_key), (message, record), (sig, signature)):
            path.write_bytes(value)
        code = subprocess.run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
             "-inkey", str(key), "-rawin", "-in", str(message), "-sigfile", str(sig)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=5,
        ).returncode
    require(code == 0, "invalid capture signature")


def signed_record(directory, name, pin):
    raw = bounded(directory / f"{name}.json", 16 * 1024)
    verify_signature(bounded(directory / f"{name}.der", 44), pin, raw,
                     bounded(directory / f"{name}.sig", 64))
    return raw, load_json(raw)


def validate_profile(profile, now):
    fields(profile, (*IMAGES, "device", "challenge", "not_before", "not_after",
                     "bl31_key_sha256", "entry_key_sha256", "shim_pc", "fdt_pa",
                     "xnu_pc", "xnu_argument", "adt_sha256"), "trusted profile")
    for name in (*IMAGES, "device", "challenge", "bl31_key_sha256", "entry_key_sha256", "adt_sha256"):
        hex_value(profile[name], 64, name)
    require(profile["bl31_key_sha256"] != profile["entry_key_sha256"],
            "the final-exit and entry witnesses must have independent keys")
    start = unsigned(profile["not_before"], "profile start")
    end = unsigned(profile["not_after"], "profile end")
    require(start <= now < end and end - start <= 900, "capture window is expired, premature or too long")
    for name, alignment in (("shim_pc", 4), ("fdt_pa", 8), ("xnu_pc", 4), ("xnu_argument", 8)):
        require(unsigned(profile[name], name) % alignment == 0, f"expected {name} is misaligned")


def validate_header(record, stage, profile, scope):
    require(record["format"] == FORMAT and record["scope"] == scope and record["board"] == BOARD,
            f"{stage}: invalid format, capture scope or board")
    require(record["stage"] == stage and record["slot"] == "b", f"{stage}: invalid stage or slot")
    for name in ("device", "challenge"):
        require(record[name] == profile[name], f"{stage}: {name} mismatch")
    fields(record["images"], IMAGES, f"{stage} image measurements")
    for name in IMAGES:
        require(record["images"][name] == profile[name], f"{stage}: measured {name} mismatch")
    hex_value(record["boot_id"], 32, "firmware boot ID")
    hex_value(record["fdt_sha256"], 64, "FDT SHA-256")
    unsigned(record["sequence"], f"{stage} sequence")


def observed_sources(directory, receipts):
    require(type(receipts) is dict and receipts.keys() <= SOURCES.keys(), "unrecognized observation class")
    for name, observation in receipts.items():
        fields(observation, ("source", "sha256"), name)
        require(observation["source"] == SOURCES[name], f"{name}: wrong observation source")
        sha = hex_value(observation["sha256"], 64, name)
        body = bounded(directory / f"{name}.bin", 2 * 1024 * 1024)
        require(digest(body) == sha, f"{name}: observation bytes differ from the signed reference")
    return sorted(receipts)


def verify(directory, profile, now, scope=PHYSICAL_SCOPE):
    validate_profile(profile, now)
    bl31_raw, bl31 = signed_record(directory, "final-bl31", profile["bl31_key_sha256"])
    entry_raw, entry = signed_record(directory, "xnu-entry", profile["entry_key_sha256"])
    fields(bl31, COMMON | {"ns_pc", "fdt_pa", "observations"}, "final BL31")
    fields(entry, COMMON | {"bl31_record_sha256", "shim_pc", "fdt_pa", "xnu_pc",
                           "xnu_argument", "adt_sha256"}, "XNU entry")
    validate_header(bl31, "final-bl31-exit", profile, scope)
    validate_header(entry, "actual-xnu-entry", profile, scope)
    require(bl31["boot_id"] == entry["boot_id"] and bl31["sequence"] < entry["sequence"],
            "boot ID mismatch or incorrect event order")
    require(entry["bl31_record_sha256"] == digest(bl31_raw), "entry did not bind this exact BL31 record")
    require(unsigned(bl31["ns_pc"], "BL31 return PC") ==
            unsigned(entry["shim_pc"], "observed shim PC") == profile["shim_pc"], "bootshim PC mismatch")
    require(unsigned(bl31["fdt_pa"], "BL31 DTB pointer") ==
            unsigned(entry["fdt_pa"], "observed DTB pointer") == profile["fdt_pa"], "incoming x0 mismatch")
    require(unsigned(entry["xnu_pc"], "observed XNU PC") == profile["xnu_pc"], "XNU entry PC mismatch")
    require(unsigned(entry["xnu_argument"], "observed XNU x0") == profile["xnu_argument"], "XNU x0 mismatch")

    fdt = bounded(directory / "incoming.dtb", 2 * 1024 * 1024)
    require(len(fdt) >= 40 and struct.unpack_from(">II", fdt) == (0xd00dfeed, len(fdt)),
            "invalid or non-exact incoming FDT span")
    require(digest(fdt) == bl31["fdt_sha256"] == entry["fdt_sha256"], "incoming DTB digest mismatch")
    adt = bounded(directory / "entry.adt", 2 * 1024 * 1024)
    require(digest(adt) == entry["adt_sha256"] == profile["adt_sha256"], "XNU entry ADT digest mismatch")
    present = observed_sources(directory, bl31["observations"])
    return {
        "scope": scope,
        "authenticated_entry_pair": True,
        "boot_id": bl31["boot_id"],
        "final_bl31_record_sha256": digest(bl31_raw),
        "xnu_entry_record_sha256": digest(entry_raw),
        "incoming_fdt_sha256": digest(fdt),
        "observations_bound": present,
        "observations_missing": sorted(SOURCES.keys() - set(present)),
        "resource_ownership_validated": False,
        "physical_ufs_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="directory containing capture files only")
    parser.add_argument("--trusted-profile", required=True, type=Path,
                        help="out-of-band operator policy and key pins, never from the capture bundle")
    args = parser.parse_args()
    try:
        capture = args.capture.resolve(strict=True)
        profile_path = args.trusted_profile.resolve(strict=True)
        require(not profile_path.is_relative_to(capture), "trusted profile must be outside the capture directory")
        result = verify(capture, load_json(bounded(profile_path, 8 * 1024)), int(time.time()))
    except (Rejected, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"handoff capture rejected: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
