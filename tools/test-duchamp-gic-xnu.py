#!/usr/bin/env python3
"""Exercise the Duchamp GIC capability in XNU on QEMU, both ways.

The positive run uses an exact QEMU-only ADT capability.  The negative run
removes that one property while preserving the rest of the ADT byte-for-byte
after reserialization.  This tool never contacts a phone or physical device.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import adt


PROPERTY = "duchamp,gic-mmio-auth-v1"
EXPECTED = (
    0x08000000,
    0x00010000,
    0x080A0000,
    0x00100000,
)
POSITIVE_MARKER = "SWEET CPU: 1/1 CPUs initialized, SGI1 verified"
NEGATIVE_MARKER = "DUCHAMP GICR scan failed -8 size=1048576"


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def walk(node, path=""):
    here = f"{path}/{node.name}" if path else f"/{node.name}"
    yield here, node
    for child in node.children:
        yield from walk(child, here)


def strip_capability(raw):
    tree, end = adt.parse(raw)
    if end != len(raw):
        raise ValueError("trailing ADT bytes")
    matches = []
    for path, node in walk(tree):
        for name, flags, value in node.props:
            if name == PROPERTY:
                matches.append((path, flags, value))
                node.props = [prop for prop in node.props if prop[0] != name]
    if len(matches) != 1:
        raise ValueError(f"expected one {PROPERTY}, found {len(matches)}")
    path, flags, value = matches[0]
    if path != "/device-tree/arm-io/gic" or flags != 0 or len(value) != 32:
        raise ValueError("unexpected GIC capability location or encoding")
    words = tuple(
        int.from_bytes(value[index:index + 8], "little")
        for index in range(0, len(value), 8)
    )
    if words != EXPECTED:
        raise ValueError(f"unexpected GIC capability values: {words}")
    stripped = adt.serialize(tree)
    if len(raw) - len(stripped) != 68:
        raise ValueError("negative ADT changed by more than one 32-byte property")
    check, check_end = adt.parse(stripped)
    if check_end != len(stripped) or any(
        name == PROPERTY
        for _, node in walk(check)
        for name, _, _ in node.props
    ):
        raise ValueError("negative ADT still contains the capability")
    return stripped, {"path": path, "values": [hex(word) for word in words]}


def run(command):
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--kernel-sha256", required=True)
    parser.add_argument("--adt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--ci-run")
    parser.add_argument("--ci-head")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    kernel = args.kernel.resolve()
    source_adt = args.adt.resolve()
    output = args.output.resolve()
    if not 20 <= args.seconds <= 600:
        parser.error("--seconds must be between 20 and 600")
    if output.exists():
        parser.error("--output must not already exist")
    kernel_before = kernel.read_bytes()
    adt_before = source_adt.read_bytes()
    if sha256(kernel_before) != args.kernel_sha256.lower():
        parser.error("kernel SHA-256 pin mismatch")
    try:
        negative_adt, removed = strip_capability(adt_before)
    except (UnicodeError, ValueError) as error:
        parser.error(str(error))

    output.mkdir(parents=True)
    tokenless = output / "boot-gic-tokenless.adt"
    tokenless.write_bytes(negative_adt)
    positive_payload = output / "payload-gic-authorized.bin"
    negative_payload = output / "payload-gic-tokenless.bin"
    cmdline = "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress sweet_console_fb=1"
    run([
        sys.executable, str(repo / "tools/mkpayload.py"), str(kernel),
        str(source_adt), str(positive_payload), "--cmdline", cmdline,
    ])
    run([
        sys.executable, str(repo / "tools/mkpayload.py"), str(kernel),
        str(tokenless), str(negative_payload), "--cmdline", cmdline,
    ])

    positive = output / "authorized"
    negative = output / "tokenless"
    base = [
        sys.executable, str(repo / "tools/qemu-sweet.py"),
    ]
    run(base + [
        str(positive_payload), str(positive), "--secs", str(args.seconds),
        "--snapshot-interval", "2", "--framebuffer", "duchamp",
        "--kernel", str(kernel), "--stop-on-text", POSITIVE_MARKER,
    ])
    run(base + [
        str(negative_payload), str(negative), "--secs", "30",
        "--snapshot-interval", "0.5", "--framebuffer", "duchamp",
        "--kernel", str(kernel), "--stop-on-text", NEGATIVE_MARKER,
    ])

    positive_text = (positive / "fb.txt").read_text(encoding="utf-8")
    negative_text = (negative / "fb.txt").read_text(encoding="utf-8")
    positive_result = json.loads((positive / "result.json").read_text())
    negative_result = json.loads((negative / "result.json").read_text())
    checks = {
        "authorized_reached_post_gic_sgi": POSITIVE_MARKER in positive_text,
        "authorized_no_panic": "panic(" not in positive_text and
            "SWEET EARLY PANIC" not in positive_text,
        "tokenless_refused_unverified": NEGATIVE_MARKER in negative_text,
        "tokenless_panicked_fail_closed": negative_result.get("status") == "panic",
        "source_adt_unchanged": source_adt.read_bytes() == adt_before,
        "kernel_unchanged": kernel.read_bytes() == kernel_before,
        "only_capability_property_removed": len(adt_before) - len(negative_adt) == 68,
    }
    report = {
        "passed": all(checks.values()),
        "checks": checks,
        "kernel_sha256": sha256(kernel_before),
        "source_adt_sha256": sha256(adt_before),
        "tokenless_adt_sha256": sha256(negative_adt),
        "removed_capability": removed,
        "positive": positive_result,
        "negative": negative_result,
        "ci_run": args.ci_run,
        "ci_head": args.ci_head,
        "safety": {
            "qemu_only": True,
            "phone_access": False,
            "physical_mmio": False,
            "partition_write": False,
        },
        "scope": "QEMU GIC capability polarity; no physical ownership claim",
    }
    (output / "verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
