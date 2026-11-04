#!/usr/bin/env python3
"""Validate the pinned XNU UFS cache-backend execution in QEMU.

The source report came from ``test-duchamp-ufs-xnu.py --backends`` and is
hash-pinned.  The exact CI commit blobs are also checked so that the success
marker remains tied to the implementation that requires one clean, one flush
and three barriers.  This is an XNU implementation proof, not MT6897 physical
cache, firmware, firewall or controller-ownership evidence.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


REPORT_VERSION = 1
RAW_SHA256 = "ecb7460c49ca0475807749b15ee9c8b88da1d7e2bd8effe5c2398632e797e373"
CI_RUN = "41740480659"
CI_HEAD = "03a3f9d0141848f3245f86598e477ad36d8ade4b"
KERNEL_SHA256 = "cbaba0812c449d67e0e3e6c718e696b52b3f43228d9f020c145e8b5b28926b30"
PAYLOAD_SHA256 = "ae2d1c41d61d81f8806dd521100325242464a0ef168da1bf3243ef8c52c9d4cc"

SOURCE_BLOBS = {
    "duchamp/xnu/mt6897_ufs_cache_backend.c":
        "4dc7247a4f4ef2ade1c3624b4a7c54c662277b6ba218a5b94f7402b6681c3b1a",
    "duchamp/xnu/mt6897_ufs_cache_backend.h":
        "450459f4a05aa4a40e39f4d05b76f6e70e8a1c66c6a929acc454703ba2cb0389",
    "duchamp/xnu/qemu_backends.c":
        "408761c168f5dc424472f4eec526e747180e72a4e95aa4898220d71ae1f15ae3",
    "duchamp/xnu/test_mt6897_ufs_cache_backend.c":
        "36e29c2c1b87a79a99a87170bff3563e9627bfcb2d5e4b732dbab56e0b8e558f",
    "tools/stage-duchamp-qemu-backends.py":
        "cf973a6ba713e4718aa9e856dd0924ac192a61d01d88f6c92d42a6ec2642eac7",
    "tools/test-duchamp-ufs-xnu.py":
        "b060426bd7b722f8a7acbe9d6ee1f89ab143294b959016fe90f0093de4a398f1",
    "tools/test-mt6897-ufs-cache-backend.py":
        "cdd04f3a09acc4aefbc2102408b103d195ec8e8217d9173b7309a5d6f2569926",
}

REQUIRED_CHECKS = (
    "QEMU RAM ROOT MOUNTED",
    "QEMU ROOTVNODE READY",
    "DUCHAMP UFS PID1 ENTERED",
    "DUCHAMP UFS PID1 heartbeat",
    "QEMU XNU FIRMWARE CONTRACT UNVERIFIED REFUSED",
    "QEMU XNU PHYSICAL PROVIDERS DEFAULT CLOSED",
    "QEMU XNU UFS LEASE PROVIDER DEFAULT CLOSED",
    "QEMU XNU UFS CACHE CONTRACT DEFAULT CLOSED",
    "QEMU XNU UFS CACHE PRIMITIVES PASS",
    "QEMU XNU UFS DMA ROUTE DEFAULT CLOSED",
    "QEMU XNU BACKENDS SELFTEST PASS",
    "DUCHAMP XNU BACKENDS PASS tables=1 mmu=1 pmic=1 fw_verified=0 physical=0",
    "runner_exit_zero",
    "no_observed_panic",
    "success_stop",
    "host_image_unchanged",
    "readonly_no_ramdisk",
    "kernel_pin_preserved",
    "compiled_adapter_symbols_present",
    "virtual_timer_irq_witness",
    "test_sources_unchanged",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_commit_sources(repo, expected=SOURCE_BLOBS):
    verified = {}
    for path, digest in expected.items():
        try:
            raw = subprocess.check_output(
                ["git", "show", CI_HEAD + ":" + path],
                cwd=repo,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as error:
            raise ValueError("cannot read pinned CI source: " + path) from error
        observed = sha256(raw)
        require(observed == digest, "pinned CI source hash differs: " + path)
        verified[path] = observed
    return verified


def validate(repo, path):
    raw = path.read_bytes()
    require(sha256(raw) == RAW_SHA256, "XNU cache QEMU result hash differs")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("XNU cache QEMU result is not valid UTF-8 JSON") from error

    require(result.get("passed") is True, "XNU cache QEMU run did not pass")
    require(result.get("backend_selftest_requested") is True,
            "cache backend selftest was not requested")
    require(result.get("ci_run") == CI_RUN and result.get("ci_head") == CI_HEAD,
            "CI provenance differs")
    require(result.get("kernel_sha256") == KERNEL_SHA256,
            "kernel hash differs")
    require(result.get("payload_sha256") == PAYLOAD_SHA256,
            "payload hash differs")
    checks = result.get("checks", {})
    require(checks and all(value is True for value in checks.values()),
            "one or more QEMU checks failed")
    for name in REQUIRED_CHECKS:
        require(checks.get(name) is True, "missing QEMU proof: " + name)

    fixture = result.get("fixture", {})
    require(fixture.get("base_unchanged") is True and
            fixture.get("readonly_backend") is True and
            fixture.get("no_ramdisk") is True,
            "QEMU fixture was not immutable/read-only")
    require(fixture.get("init_source_sha256") ==
            result.get("test_source_hashes", {}).get(
                "tools/duchamp-backend-init.S"),
            "diagnostic init provenance differs")
    require(result.get("physical_diagnostics_read_only") is True,
            "physical diagnostics were not read-only")
    require(result.get("execution", {}).get("hardware_timing_claimed") is False,
            "QEMU result overclaims hardware timing")
    timer = result.get("timer_irq_witness", {})
    require(timer.get("passed") is True and
            timer.get("matching_pixels") == timer.get("expected_pixels") == 512,
            "virtual timer IRQ witness differs")
    scope = result.get("scope", "")
    require(isinstance(scope, str) and "no physical phone/backend" in scope,
            "result scope does not keep the physical backend disabled")

    source_blobs = verify_commit_sources(repo)
    require(result.get("test_source_hashes", {}).get(
                "tools/test-duchamp-ufs-xnu.py") ==
            SOURCE_BLOBS["tools/test-duchamp-ufs-xnu.py"],
            "QEMU runner source hash differs")

    return {
        "report_version": REPORT_VERSION,
        "passed": True,
        "verdict": "validated-xnu-cache-primitives-in-qemu",
        "proven": {
            "actual_xnu_kernel_executed": True,
            "lease_bound_cache_backend_linked": True,
            "clean_to_poc_callback_executed": True,
            "flush_to_poc_callback_executed": True,
            "barrier_sequence_executed": True,
            "expected_clean_calls": 1,
            "expected_flush_calls": 1,
            "expected_barrier_calls": 3,
            "fail_closed_physical_provider_path": True,
            "read_only_hfs_root_mounted": True,
            "pid1_reached": True,
            "no_kernel_panic_observed": True,
        },
        "not_proven": {
            "mt6897_outer_or_system_cache_reachability": False,
            "mt6897_physical_cache_owner": False,
            "firmware_or_firewall_delegation": False,
            "ufs_controller_resource_ownership": False,
        },
        "inputs": {
            "raw_result_sha256": RAW_SHA256,
            "ci_run": CI_RUN,
            "ci_head": CI_HEAD,
            "kernel_sha256": KERNEL_SHA256,
            "payload_sha256": PAYLOAD_SHA256,
            "ci_source_blobs": source_blobs,
        },
        "safety": {
            "qemu_only": True,
            "phone_access": False,
            "mmio_access_on_phone": False,
            "smc_execution_on_phone": False,
            "partition_access": False,
            "physical_ufs_backend_enabled": False,
        },
        "scope": (
            "actual XNU clean/flush/barrier callback execution in QEMU; "
            "not MT6897 physical cache or resource ownership"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    report = validate(repo, args.result.resolve(strict=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
