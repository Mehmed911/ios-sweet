#!/usr/bin/env python3
"""Tie the running Duchamp BL31 identity to the captured tee_a sample.

This is an offline evidence producer.  It validates the exact tee_a capture,
extracts the packaged ATF identity strings, validates the exact bounded ATF
runtime log and its capture report, and requires all four identities to match.

The result proves a runtime identity-string match.  It deliberately does not
claim byte-for-byte equivalence with the installed firmware, SMC effects,
firewall state, resource ownership, or physical UFS readiness.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct


REPORT_VERSION = 1
TEE_BYTES = 5 * 1024 * 1024
TEE_SHA256 = "37d7d5acbe02289465af9702cbcafb1986394332a3462badda398556d32e587d"
ATF_BYTES = 0xE8E78
ATF_SHA256 = "716222a632e4a0623a2e467e17f1d36f38a37f79a1c026447fe724e75e90e07e"
RUNTIME_LOG_BYTES = 1246
RUNTIME_LOG_SHA256 = "120954e0698210350ad81c6151311ae4adcf805e1054818352e5908f4c60bd66"
RUNTIME_REPORT_SHA256 = "764ab81f5f831ebf993a0263cc7702cda79426326247b3c4e8c84278713fa895"
PINNED_VERIFICATION_SHA256 = (
    "1a9060eec770e72f70d1e51b2d0e8b86ab5be45b0ccd6ca73ca6b345171dcba2"
)

OUTER_MAGIC = 0x58881688
INNER_MAGIC = 0x58891689
ATF_HEADER_BYTES = 0x200

IDENTITY = {
    "release": "lts-v2.8.6(release):2fbca47",
    "built": "07:19:18, Dec 18 2024",
    "software_version": "common_2.6.1(6897-1.2)",
    "software_build": "Jun 8 2022(Jul 25 20:00:00 UTC 2023)",
}

BINARY_STRINGS = {
    "release": IDENTITY["release"],
    "built": "Built : " + IDENTITY["built"],
    "software": "common_2.6.1",
    "platform": "6897-1.2",
    "software_built": "Jun 8 2022",
    "software_build_host_time": "Jul 25 20:00:00 UTC 2023",
}

RUNTIME_PATTERNS = {
    "release": r"^NOTICE:\s+\(0\)\[[^\]]+\]BL31: (?!Built :)([^\r\n]+)$",
    "built": r"^NOTICE:\s+\(0\)\[[^\]]+\]BL31: Built : ([^\r\n]+)$",
    "software_version": r"^NOTICE:\s+\(0\)\[[^\]]+\]Software version: ([^\r\n]+)$",
    "software_build": r"^NOTICE:\s+\(0\)\[[^\]]+\]Build time: ([^\r\n]+)$",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def u32(raw, offset):
    require(offset >= 0 and offset + 4 <= len(raw), "truncated 32-bit field")
    return struct.unpack_from("<I", raw, offset)[0]


def c_string(raw, offset, width):
    require(offset >= 0 and offset + width <= len(raw),
            "truncated string field")
    value = raw[offset:offset + width].split(b"\0", 1)[0]
    try:
        return value.decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("non-ASCII package string") from error


def unique_offset(raw, text, start, end, label):
    encoded = text.encode("ascii")
    first = raw.find(encoded, start, end)
    require(first >= 0, "missing captured BL31 identity: " + label)
    require(raw.find(encoded, first + 1, end) < 0,
            "duplicate captured BL31 identity: " + label)
    return first


def extract_captured_identity(tee):
    require(len(tee) == TEE_BYTES, "tee_a size differs")
    require(sha256(tee) == TEE_SHA256, "tee_a SHA-256 differs")
    require(u32(tee, 0) == OUTER_MAGIC, "tee_a ATF outer magic differs")
    require(u32(tee, 4) == ATF_BYTES, "tee_a ATF size differs")
    require(c_string(tee, 8, 32) == "atf", "tee_a first entry is not ATF")
    require(u32(tee, 0x30) == INNER_MAGIC, "tee_a ATF inner magic differs")
    require(u32(tee, 0x34) == ATF_HEADER_BYTES,
            "tee_a ATF payload offset differs")
    start = ATF_HEADER_BYTES
    end = start + ATF_BYTES
    require(end <= len(tee), "tee_a ATF payload is truncated")
    atf = tee[start:end]
    require(sha256(atf) == ATF_SHA256, "packaged ATF SHA-256 differs")
    offsets = {
        name: unique_offset(tee, text, start, end, name)
        for name, text in BINARY_STRINGS.items()
    }
    return dict(IDENTITY), offsets, atf


def extract_runtime_identity(log):
    require(len(log) == RUNTIME_LOG_BYTES, "runtime ATF log size differs")
    require(sha256(log) == RUNTIME_LOG_SHA256,
            "runtime ATF log SHA-256 differs")
    try:
        text = log.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("runtime ATF log is not UTF-8") from error
    identity = {}
    for name, pattern in RUNTIME_PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.MULTILINE)
        require(len(matches) == 1,
                "runtime ATF identity occurrence differs: " + name)
        identity[name] = matches[0]
    return identity


def validate_runtime_report(raw):
    require(sha256(raw) == RUNTIME_REPORT_SHA256,
            "runtime capture report SHA-256 differs")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("runtime capture report is not valid JSON") from error
    require(report.get("passed") is True, "runtime capture did not pass")
    target = report.get("target", {})
    require(target.get("device") == "duchamp" and
            target.get("hardware") == "mt6897",
            "runtime capture target differs")
    receipt = report.get("receipts", {}).get(
        "root-atf_log_head.stdout.txt", {}
    )
    require(receipt == {
        "bytes": RUNTIME_LOG_BYTES,
        "sha256": RUNTIME_LOG_SHA256,
    }, "runtime ATF log receipt differs")
    require(report.get("firmware", {}).get(
                "installed_bl31_identity", {}).get("status") == "observed",
            "runtime report did not observe BL31 identity")
    safety = report.get("safety", {})
    require(safety.get("device_writes") is False and
            safety.get("partition_access") is False and
            safety.get("mmio_access") is False and
            safety.get("fastboot_access") is False,
            "runtime capture safety differs")
    return report


def validate_pinned_report(raw):
    require(sha256(raw) == PINNED_VERIFICATION_SHA256,
            "pinned BL31 verification SHA-256 differs")
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("pinned BL31 verification is not valid JSON") from error
    proofs = report.get("proofs", {})
    safety = report.get("safety", {})
    require(report.get("report_version") == REPORT_VERSION and
            report.get("passed") is True and
            report.get("verdict") ==
            "installed-bl31-runtime-identity-matched",
            "pinned BL31 verification verdict differs")
    require(report.get("identity") == IDENTITY,
            "pinned BL31 identity differs")
    require(proofs.get("captured_bl31_identity_extracted") is True and
            proofs.get("running_bl31_identity_observed") is True and
            proofs.get("all_identity_fields_match") is True and
            proofs.get("installed_firmware_identity_proven") is True and
            proofs.get("installed_binary_byte_equivalence_proven") is False and
            proofs.get("runtime_smc_effect_contract_proven") is False and
            proofs.get("physical_resource_ownership_proven") is False,
            "pinned BL31 proof scope differs")
    require(safety.get("offline_inputs_only") is True and
            safety.get("phone_access_by_this_tool") is False and
            safety.get("firmware_executed_by_this_tool") is False and
            safety.get("smc_execution") is False and
            safety.get("mmio_access") is False and
            safety.get("partition_access") is False and
            safety.get("physical_ufs_backend_enabled") is False,
            "pinned BL31 verification safety differs")
    return report


def build_report(tee, runtime_log, runtime_report_raw):
    captured, offsets, atf = extract_captured_identity(tee)
    running = extract_runtime_identity(runtime_log)
    runtime_report = validate_runtime_report(runtime_report_raw)
    reported = runtime_report["firmware"]["installed_bl31_identity"]
    reported_identity = {
        "release": reported.get("release"),
        "built": reported.get("built"),
        "software_version": reported.get("software_version"),
        "software_build": reported.get("software_build_time"),
    }
    require(captured == running == reported_identity == IDENTITY,
            "captured, running and reported BL31 identities differ")
    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "verdict": "installed-bl31-runtime-identity-matched",
        "identity": dict(IDENTITY),
        "capture": {
            "tee_a_bytes": len(tee),
            "tee_a_sha256": sha256(tee),
            "atf_bytes": len(atf),
            "atf_sha256": sha256(atf),
            "identity_string_offsets": offsets,
        },
        "runtime": {
            "atf_log_bytes": len(runtime_log),
            "atf_log_sha256": sha256(runtime_log),
            "capture_report_sha256": sha256(runtime_report_raw),
            "device_serial_sha256": runtime_report.get(
                "device_serial_sha256"
            ),
        },
        "proofs": {
            "captured_bl31_identity_extracted": True,
            "running_bl31_identity_observed": True,
            "all_identity_fields_match": True,
            "installed_firmware_identity_proven": True,
            "installed_binary_byte_equivalence_proven": False,
            "runtime_smc_effect_contract_proven": False,
            "physical_resource_ownership_proven": False,
        },
        "safety": {
            "offline_inputs_only": True,
            "phone_access_by_this_tool": False,
            "firmware_executed_by_this_tool": False,
            "smc_execution": False,
            "mmio_access": False,
            "partition_access": False,
            "physical_ufs_backend_enabled": False,
        },
        "scope": (
            "exact runtime BL31 identity strings matched the captured tee_a "
            "ATF entry; not byte equivalence, SMC effects, firewall state, "
            "resource ownership or physical UFS authorization"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tee_image", type=Path)
    parser.add_argument("runtime_log", type=Path)
    parser.add_argument("runtime_report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        output = args.output.resolve()
        require(not output.exists(), "preserve existing output: " + str(output))
        report = build_report(
            args.tee_image.resolve(strict=True).read_bytes(),
            args.runtime_log.resolve(strict=True).read_bytes(),
            args.runtime_report.resolve(strict=True).read_bytes(),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except (OSError, ValueError) as error:
        parser.exit(1, "BL31 identity verification failed: " + str(error) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
