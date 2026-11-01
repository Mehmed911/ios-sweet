#!/usr/bin/env python3
"""Verify a hash-pinned full-XNU pre-GIC counter-probe QEMU run."""

import argparse
import hashlib
import json
from pathlib import Path


PASS_MARKER = "DUCHAMP COUNTER PROBE PASS"
FAIL_MARKERS = (
    "DUCHAMP COUNTER PROBE FAIL",
    "panic(cpu ",
    "SWEET EARLY PANIC:",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run, kernel, payload, adt, expected):
    actual = {
        "kernel": sha256(kernel),
        "payload": sha256(payload),
        "adt": sha256(adt),
    }
    for name, digest in expected.items():
        require(actual[name] == digest, name + " SHA-256 differs")

    result_path = run / "result.json"
    screen_path = run / "fb.txt"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    screen = screen_path.read_text(encoding="utf-8")

    require(result.get("stop_marker") == PASS_MARKER,
            "QEMU did not stop on the counter PASS marker")
    require(result.get("status") in ("no_panic_observed", "incomplete_decode"),
            "unexpected QEMU screen status")
    require(isinstance(result.get("unknown_glyphs"), int),
            "missing unknown-glyph count")
    require(result["unknown_glyphs"] >= 0, "invalid unknown-glyph count")
    execution = result.get("execution", {})
    require(execution.get("hardware_timing_claimed") is False,
            "QEMU result promoted a hardware-timing claim")

    require(screen.count(PASS_MARKER) == 1,
            "counter PASS marker is missing or duplicated")
    require("SWEET EARLY 20: kprintf startup complete" in screen,
            "pre-probe console checkpoint is missing")
    require("SWEET EARLY 23: " + PASS_MARKER in screen,
            "counter PASS checkpoint number differs")
    for marker in FAIL_MARKERS:
        require(marker not in screen, "failure marker observed: " + marker)

    return {
        "passed": True,
        "verdict": "full-xnu-pre-gic-counter-probe-passed-in-qemu",
        "inputs": {
            "kernel_sha256": actual["kernel"],
            "payload_sha256": actual["payload"],
            "adt_sha256": actual["adt"],
        },
        "evidence": {
            "stop_marker": result["stop_marker"],
            "screen_status": result["status"],
            "unknown_glyphs": result["unknown_glyphs"],
            "elapsed_host_seconds": result.get("elapsed_host_seconds"),
            "result_sha256": sha256(result_path),
            "framebuffer_text_sha256": sha256(screen_path),
            "checkpoint_20_observed": True,
            "checkpoint_23_pass_observed": True,
        },
        "scope": {
            "qemu_only": True,
            "phone_access": False,
            "mmio_to_phone": False,
            "smc_execution": False,
            "partition_access": False,
            "hardware_timer_proven": False,
            "gic_ownership_proven": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--adt", type=Path, required=True)
    parser.add_argument("--kernel-sha256", required=True)
    parser.add_argument("--payload-sha256", required=True)
    parser.add_argument("--adt-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = verify(
        args.run.resolve(), args.kernel.resolve(), args.payload.resolve(),
        args.adt.resolve(), {
            "kernel": args.kernel_sha256.lower(),
            "payload": args.payload_sha256.lower(),
            "adt": args.adt_sha256.lower(),
        })
    if args.output:
        output = args.output.resolve()
        if output.exists():
            parser.error("preserve existing output")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
