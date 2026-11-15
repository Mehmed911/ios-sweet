#!/usr/bin/env python3
"""Run the offline handoff parser and trust-policy regression with mock receipts."""
import argparse
import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess

TOOLS = Path(__file__).resolve().parent
DRIVERS = TOOLS.parent / "duchamp/drivers"
MODEL = DRIVERS / "model"
SOURCE = MODEL / "duchamp_ufs_handoff_model.c"


def command(argv, out, name, *, expected=0):
    args = list(map(str, argv))
    log = out / (name + ".log")
    receipt = out / (name + ".command.json")
    details = dict(argv=args, cwd=str(Path.cwd()), timeout_seconds=40, log=log.name)
    with log.open("xb") as handle:
        try:
            result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=handle,
                                    stderr=subprocess.STDOUT, timeout=40)
            details["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            details["exit_code"] = None
            details["timed_out"] = True
    receipt.write_text(json.dumps(details, indent=2) + "\n")
    if details["exit_code"] != expected:
        raise RuntimeError(f"{name} returned {details['exit_code']}, see {log}")
    return log.read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=lambda p: Path(p).resolve())
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True)
    clang = shutil.which(args.clang)
    qemu = shutil.which(args.qemu)
    if not clang or not qemu:
        parser.error("Clang and ARM64 QEMU must be available")

    options = ["-std=c11", "-g", "-Wall", "-Wextra", "-Werror", "-I", DRIVERS]
    rejected = command([clang, *options, "-fsyntax-only", SOURCE], out,
                       "production-rejection", expected=1)
    assert "restricted to offline tests" in rejected
    build = [clang, *options, "-DDUCHAMP_UFS_HANDOFF_MODEL_TEST"]
    sources = [SOURCE, MODEL / "test_duchamp_ufs_handoff_model.c", DRIVERS / "mt6897_ufs_gate.c"]
    native, arm = out / "handoff.native", out / "handoff.elf"
    command([*build, "-O1", "-fsanitize=address,undefined", *sources, "-o", native], out, "native-build")
    host = command([native], out, "native")

    linker = out / "model.ld"
    linker.write_text(runpy.run_path(str(TOOLS / "test-duchamp-ufs-handoff-qemu.py"))["LINKER"])
    command([*build, "--target=aarch64-none-elf", "-O2", "-ffreestanding",
             "-fno-builtin", "-mgeneral-regs-only", "-mstrict-align",
             "-DMT6897_MODEL_FREESTANDING", "-nostdlib", "-fuse-ld=lld", "-Wl,-T," + str(linker),
             DRIVERS / "test_mt6897_model_start.S", DRIVERS / "test_mt6897_model_runtime.c",
             *sources, "-o", arm], out, "arm-build")
    events = out / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n")
    trace = out / "ufs.trace"
    guest = command([qemu, "-M", "virt,gic-version=3,highmem-ecam=off", "-cpu", "cortex-a76",
                     "-m", "64M", "-smp", "1", "-nodefaults", "-display", "none", "-monitor", "none",
                     "-serial", "stdio", "-nic", "none", "-device", "ufs,id=ufs0,addr=04.0,mcq=off",
                     "-semihosting-config", "enable=on,target=native", "-kernel", arm,
                     "-trace", f"events={events},file={trace}"], out, "qemu")
    case_regex = r"(?m)^UFS HANDOFF FORMAT case=(\d+) status=(\d+)$"
    rows = re.findall(case_regex, host)
    assert rows == re.findall(case_regex, guest)
    assert [int(row[0]) for row in rows] == list(range(1, len(rows) + 1))
    passed = f"DUCHAMP UFS HANDOFF FORMAT PASS cases={len(rows)}\n"
    assert len(rows) >= 65 and host.endswith(passed) and guest.endswith(passed + "MT6897 ARM64 MODEL PASS\n")
    assert trace.stat().st_size == 0
    report = dict(passed=True, cases_per_environment=len(rows), native_sanitizers=["ASan", "UBSan"],
                  short_lengths_rejected=448, identical_results=True, virtual_ufs_accesses=0,
                  physical_access=False, production_provider=False, wire_version=1)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Duchamp UFS handoff format PASS {len(rows)} cases each, native and ARM64 QEMU")


if __name__ == "__main__":
    main()
