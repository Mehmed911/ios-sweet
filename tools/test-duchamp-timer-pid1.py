#!/usr/bin/env python3
"""Require a real timer IRQ acknowledgement and a diagnostic PID 1 in QEMU."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


TIMER_MARKER = "SWEET TIMER PPI27 IRQ CONFIRMED"
PE_IOKIT_MARKERS = (
    "SWEET EARLY 127: InitIOKit entering",
    "SWEET EARLY 128: InitIOKit returned",
    "SWEET EARLY 129: DUCHAMP PRE CONFIGURE IOKIT",
    "SWEET EARLY 130: ConfigureIOKit entering",
    "SWEET EARLY 131: ConfigureIOKit returned",
    "SWEET EARLY 132: DUCHAMP POST CONFIGURE IOKIT",
    "SWEET EARLY 133: PE init iokit returned",
)
PID1_MARKER = "*** SWEET userspace: init running as PID 1 ***"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kernel", "adt", "base-hfs", "base-init", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=120)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    out = args.output.resolve()
    if out.exists():
        parser.error("refusing to overwrite an existing evidence directory")
    for path in (args.kernel, args.adt, args.base_hfs, args.base_init):
        if not path.is_file():
            parser.error("missing input: " + str(path))

    input_hashes = {
        "kernel": sha256(args.kernel),
        "adt": sha256(args.adt),
        "base_hfs": sha256(args.base_hfs),
        "base_init": sha256(args.base_init),
    }
    out.mkdir(parents=True)
    subprocess.run(
        ["sh", str(repo / "tools/build-sweet-userland.sh"), str(out)],
        check=True,
    )
    subprocess.run(
        [
            "python3",
            str(repo / "tools/replace-embedded-file.py"),
            str(args.base_hfs.resolve()),
            str(args.base_init.resolve()),
            str(out / "launchd"),
            str(out / "root.hfs"),
        ],
        check=True,
    )

    cmdline = (
        "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam "
        "-noprogress rd=md0 rootrw=1 sweet_console_fb=1 "
        "duchamp_timer_irq_ack=1"
    )
    subprocess.run(
        [
            "python3",
            str(repo / "tools/mkpayload.py"),
            str(args.kernel.resolve()),
            str(args.adt.resolve()),
            str(out / "payload.bin"),
            "--ramdisk",
            str(out / "root.hfs"),
            "--cmdline",
            cmdline,
        ],
        check=True,
    )

    run = out / "run"
    command = [
        "python3",
        str(repo / "tools/qemu-sweet.py"),
        str(out / "payload.bin"),
        str(run),
        "--secs",
        str(args.seconds),
        "--framebuffer",
        "duchamp",
        "--kernel",
        str(args.kernel.resolve()),
        "--snapshot-interval",
        "1",
        "--stop-on-text",
        PID1_MARKER,
        "--stop-on-text",
        "SWEET EARLY PANIC:",
        "--fail-on-panic",
    ]
    (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    qemu_exit = subprocess.run(command).returncode

    frame_paths = sorted((run / "frames").glob("*.txt"))
    if (run / "fb.txt").is_file():
        frame_paths.append(run / "fb.txt")
    frames = [path.read_text(errors="replace") for path in frame_paths]
    combined = "\n".join(frames)
    result = json.loads((run / "result.json").read_text())
    witness_process = subprocess.run(
        [
            "python3",
            str(repo / "tools/verify-duchamp-timer-irq-witness.py"),
            str(run / "fb.png"),
        ],
        text=True,
        capture_output=True,
    )
    try:
        timer_witness = json.loads(witness_process.stdout)
    except (json.JSONDecodeError, TypeError):
        timer_witness = {
            "passed": False,
            "error": "timer witness verifier emitted invalid JSON",
        }
    timer_witness["process_exit"] = witness_process.returncode
    if witness_process.stderr:
        timer_witness["stderr"] = witness_process.stderr[-2000:]
    checks = {
        "qemu_exit_zero": qemu_exit == 0,
        "no_visible_panic": result.get("status") == "no_panic_observed"
        and "SWEET EARLY PANIC:" not in combined,
        "timer_ppi27_irq_witness": witness_process.returncode == 0
        and timer_witness.get("passed") is True,
        "pe_iokit_trace_complete": all(marker in combined for marker in PE_IOKIT_MARKERS),
        "ram_root_mounted": "QEMU RAM ROOT MOUNTED" in combined,
        "root_vnode_ready": "QEMU ROOTVNODE READY" in combined,
        "diagnostic_pid1_entered": PID1_MARKER in combined
        and result.get("stop_marker") == PID1_MARKER,
        "base_hfs_unchanged": sha256(args.base_hfs) == input_hashes["base_hfs"],
        "base_init_unchanged": sha256(args.base_init) == input_hashes["base_init"],
        "kernel_unchanged": sha256(args.kernel) == input_hashes["kernel"],
        "adt_unchanged": sha256(args.adt) == input_hashes["adt"],
    }
    report = {
        "passed": all(checks.values()),
        "checks": checks,
        "input_sha256": input_hashes,
        "output_sha256": {
            name: sha256(out / name)
            for name in ("launchd", "sweet-worker.macho", "root.hfs", "payload.bin")
        },
        "root_bytes": (out / "root.hfs").stat().st_size,
        "payload_bytes": (out / "payload.bin").stat().st_size,
        "frames_examined": len(frame_paths),
        "qemu": result,
        "observations": {
            "timer_ppi27_text_ack_visible": TIMER_MARKER in combined,
            "pe_iokit_markers": {
                marker: marker in combined for marker in PE_IOKIT_MARKERS
            },
        },
        "timer_irq_witness": timer_witness,
        "scope": (
            "QEMU timer PPI acknowledgement plus RAM-root PID 1 only; "
            "no phone, partition, UFS, or physical MMIO access"
        ),
    }
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
