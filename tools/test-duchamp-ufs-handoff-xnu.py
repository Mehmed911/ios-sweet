#!/usr/bin/env python3
"""Verify the opt-in handoff gate in an XNU replay or a full build against QEMU UFS."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import struct
import subprocess
import sys

import adt
from duchamp_ufs_xnu_replay import build_replay, digest, symbols
import mkpayload
import qemu_ufs

TOOLS = Path(__file__).resolve().parent
CASES = {
    "matched": (True, 0x3f, 0, 1),
    "different_boot": (False, 0x3f, 0, 2),
    "missing_queues": (True, 0x3b, 0, 3),
    "busy_queue": (True, 0x3f, 1, 3),
    "missing_dma": (True, 0x2f, 0, 4),
    "missing_cache": (True, 0x1f, 0, 5),
    "missing_bl31": (None, 0, 0, 6),
}
HEARTBEAT = "DUCHAMP UFS PID1 heartbeat"
DENIED = "DUCHAMP QUFS root unavailable: 1"


def make_wrapper(folder, qemu, *, entry_loaders=None, extra_events=()):
    """Add an independent device trace and use sparse host RAM for parallel guests."""
    bin_dir = folder / "bin"
    bin_dir.mkdir()
    events = folder / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\nscsi_req_parsed_lba\n" +
                      "".join(event + "\n" for event in extra_events))
    trace = folder / "ufs.trace"
    memory = folder / "guest-memory"
    path = bin_dir / "qemu-system-aarch64"
    path.write_text(f"""#!{sys.executable}
import os, sys
real = {qemu!r}
args = sys.argv[1:]
entry_loaders = {entry_loaders!r}
if "-M" in args and "-m" in args:
    machine = args.index("-M") + 1
    size = args[args.index("-m") + 1]
    args[machine] += ",memory-backend=duchamp_replay_ram"
    for option in ("-d", "-D"):
        if option in args:
            at = args.index(option)
            del args[at:at+2]
    if entry_loaders is not None:
        loaders = [i for i in range(len(args) - 1)
                   if args[i] == "-device" and args[i + 1].startswith("loader,")]
        if len(loaders) != 3 or not all(marker in args[i + 1] for i, marker in
                zip(loaders, ("/ram.bin,", "/stub.bin,", ",cpu-num=0"))):
            sys.exit("unexpected direct QEMU entry arguments")
        for index in reversed(loaders):
            del args[index:index + 2]
        args.extend(entry_loaders)
    args += ["-object", f"memory-backend-file,id=duchamp_replay_ram,size={{size}},mem-path={memory},share=on,prealloc=off",
             "-trace", "events={events},file={trace}"]
os.execv(real, [real, *args])
""")
    path.chmod(0o755)
    return bin_dir, trace, memory


def run_guest(folder, packed, kernel, disk, qemu, seconds, *, entry_loaders=None, extra_events=()):
    bin_dir, trace, memory = make_wrapper(folder, qemu, entry_loaders=entry_loaders,
                                          extra_events=extra_events)
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}")
    run = folder / "run"
    command = [sys.executable, str(TOOLS / "qemu-sweet.py"), str(packed), str(run),
               "--kernel", str(kernel), "--framebuffer", "duchamp", "--ufs-image", str(disk),
               "--secs", str(seconds), "--snapshot-interval", "1",
               "--stop-on-text", HEARTBEAT, "--stop-on-text", DENIED,
               "--stop-on-text", "SWEET EARLY PANIC:"]
    try:
        with (folder / "runner.log").open("w") as log:
            subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=seconds + 35)
    finally:
        memory.unlink(missing_ok=True)
    screens = sorted((run / "frames").glob("*.txt"))
    screen = "\n".join(path.read_text() for path in [*screens, run / "fb.txt"])
    result = json.loads((run / "result.json").read_text())
    metadata = json.loads((run / "ufs-input.json").read_text())
    return screen, trace.read_text(), result, metadata


def run_case(name, spec, ids, output, kernel, base_adt, disk, qemu, seconds):
    same_boot, proof, busy, expected = spec
    entry_id = ids[name]
    bl31_id = 0 if same_boot is None else entry_id if same_boot else ids["matched"]
    folder = output / name
    folder.mkdir()
    tree, end = adt.parse(base_adt)
    assert end == len(base_adt)
    chosen = qemu_ufs.child(tree, "chosen")
    assert chosen.prop("qemu-bl31-ufs") is None
    if bl31_id:
        fixture = struct.pack("<IIQ8I2Q", 1, proof, bl31_id,
                              1, 0, busy, 0, 0, 0, 0, 0, 5, 6)
        chosen.props.append(("qemu-bl31-ufs", 0, fixture))
    adt_path = folder / "boot.adt"
    adt_path.write_bytes(adt.serialize(tree))
    cmdline = ("debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress "
               "rd=qufs0 rootrw=0 sweet-qemu-ufs=1 sweet_console_fb=1 "
               f"sweet-qemu-ufs-handoff=1 sweet-qemu-boot-id={entry_id:#x}")
    payload, _ = mkpayload.build(kernel, adt_path, cmdline)
    packed = folder / "payload.bin"
    packed.write_bytes(payload)

    screen, text, result, metadata = run_guest(folder, packed, kernel, disk, qemu, seconds)
    seen = set(re.findall(r"UFS XNU=([0-9a-f]{16}) BL31=([0-9a-f]{16}) V=(\d+)",
                          screen, re.I))
    expected_record = (f"{entry_id:016x}", f"{bl31_id:016x}", str(expected))
    assert seen == {expected_record}, (name, seen)
    assert metadata["readonly"] and metadata["no_ramdisk"]
    if expected == 1:
        assert result["stop_marker"] == HEARTBEAT and "DUCHAMP UFS ROOT DEVICE MATCH" in screen
        assert "DUCHAMP UFS PID1 READ PASS" in screen
        assert re.search(r"ufs_exec_scsi_cmd .*opcode 0x88", text)
    else:
        assert DENIED in screen and "DUCHAMP UFS PID1 READ PASS" not in screen
        assert not text.strip(), (name, text[:600])
    return dict(entry_boot_id=hex(entry_id), bl31_boot_id=hex(bl31_id), verdict=expected,
                xnu_marker_observed=True, ufs_trace_events=len(text.splitlines()),
                storage_reached=bool(text), expected_root_failure=expected != 1,
                stop_marker=result["stop_marker"], elapsed_seconds=result["elapsed_host_seconds"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--full-build-sha256",
                        help="verify and boot the full-build Mach-O without applying replay hooks")
    parser.add_argument("--ci-run", type=int, help="provenance of the full-build artifact")
    parser.add_argument("--ci-head", help="source commit from the full-build artifact")
    parser.add_argument("--fixture", type=Path, required=True,
                        help="existing GPT UFS PID1 fixture directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--case", action="append", choices=CASES)
    args = parser.parse_args()
    qemu = shutil.which("qemu-system-aarch64")
    if qemu is None:
        parser.error("qemu-system-aarch64 is required")
    output = args.output.resolve()
    output.mkdir(parents=True)
    fixture = args.fixture.resolve()
    disk = fixture / "root.gpt.raw"
    base_adt = (fixture / "qemu-ufs.adt").read_bytes()
    disk_sha = digest(disk.read_bytes())
    manifest = json.loads((fixture / "fixture.json").read_text())
    assert disk_sha == manifest["sha256"][disk.name]
    assert digest(base_adt) == manifest["sha256"]["qemu-ufs.adt"]
    base = args.kernel.resolve()
    base_sha = digest(base.read_bytes())
    full_build = args.full_build_sha256 is not None
    if full_build:
        if base_sha != args.full_build_sha256:
            parser.error("full-build kernel SHA-256 differs from the pinned artifact")
        required = {"_arm_init", "_duchamp_qemu_ufs_handoff_enter",
                    "_duchamp_qemu_ufs_handoff_allows", "_duchamp_qemu_ufs_rootdev"}
        if not required <= symbols(base).keys():
            parser.error("full-build artifact lacks the staged XNU handoff integration")
        kernel = base
        build = dict(kernel_sha256=base_sha, ci_run=args.ci_run, ci_head=args.ci_head,
                     replay_hooks_applied=False)
    else:
        if args.ci_run is not None or args.ci_head is not None:
            parser.error("CI provenance flags require --full-build-sha256")
        kernel, build = build_replay(base, output)
    cases = args.case or list(CASES)
    if len(cases) != len(set(cases)):
        parser.error("select each case at most once")
    ids = {name: secrets.randbits(62) | (1 << 62) for name in CASES}
    assert len(set(ids.values())) == len(ids)
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(run_case, name, CASES[name], ids, output, kernel, base_adt, disk, qemu,
                               args.seconds): name for name in cases}
        for future in concurrent.futures.as_completed(pending):
            name = pending[future]
            results[name] = future.result()
            print(name, json.dumps(results[name]), flush=True)
    assert digest(base.read_bytes()) == base_sha
    assert digest(disk.read_bytes()) == disk_sha
    report = dict(passed=True, full_matrix=set(cases) == CASES.keys(), cases=results,
                  build=build, synthetic_bl31=True, actual_xnu=True, full_kernel_rebuild=full_build,
                  disk_readonly_unchanged=True, phone_access=False, partition_write=False)
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
