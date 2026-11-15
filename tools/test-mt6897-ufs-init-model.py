#!/usr/bin/env python3
"""Build the Duchamp initialization policy with mock hardware on host and ARM64."""

import argparse
import json
import re
import runpy
import subprocess
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
DRIVERS = TOOLS.parent / "duchamp/drivers"
MODEL = DRIVERS / "model"
SOURCES = [MODEL / "mt6897_ufs_init_model.c", DRIVERS / "mt6897_ufs_gate.c",
           DRIVERS / "mt6897_ufs_provider.c", MODEL / "test_mt6897_ufs_init_model.c"]


def command(args, log):
    result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=40)
    log.write_text(result.stdout)
    result.check_returncode()
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=lambda p: Path(p).resolve())
    parser.add_argument("--clang", default="clang")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True)

    options = ["-std=c11", "-g", "-Wall", "-Wextra", "-Werror", "-I", str(DRIVERS)]
    reject = subprocess.run([args.clang, *options, "-fsyntax-only", SOURCES[0]],
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=15)
    (out / "production-rejection.log").write_text(reject.stderr)
    assert reject.returncode and "restricted to offline tests" in reject.stderr
    build = [args.clang, *options, "-DMT6897_UFS_INIT_MODEL_TEST"]
    native, arm = out / "init.native", out / "init.elf"
    command([*build, "-O1", "-fsanitize=address,undefined", *SOURCES, "-o", native], out / "native-build.log")
    host = command([native], out / "native.log")

    linker = out / "model.ld"
    linker.write_text(runpy.run_path(str(TOOLS / "test-duchamp-ufs-handoff-qemu.py"))["LINKER"])
    start = DRIVERS / "test_mt6897_model_start.S"
    runtime = DRIVERS / "test_mt6897_model_runtime.c"
    command([*build, "--target=aarch64-none-elf", "-O2", "-ffreestanding", "-fno-builtin",
             "-mgeneral-regs-only", "-mstrict-align", "-DMT6897_MODEL_FREESTANDING",
             "-nostdlib", "-fuse-ld=lld", "-Wl,-T," + str(linker), start, runtime,
             *SOURCES, "-o", arm], out / "arm-build.log")
    events = out / "trace-events"
    events.write_text("ufs_mmio_read\nufs_mmio_write\nufs_exec_scsi_cmd\n")
    trace = out / "qemu-ufs.trace"
    guest = command([args.qemu, "-M", "virt,gic-version=3,highmem-ecam=off", "-cpu", "cortex-a76",
                     "-m", "64M", "-smp", "1", "-nodefaults", "-display", "none", "-monitor", "none",
                     "-serial", "stdio", "-nic", "none", "-device", "ufs,id=ufs0,addr=04.0,mcq=off",
                     "-semihosting-config", "enable=on,target=native", "-kernel", arm,
                     "-trace", f"events={events},file={trace}"], out / "qemu.log")
    rows = re.findall(r"(?m)^UFS INIT case=.*$", host)
    assert len(rows) == 67 and rows == re.findall(r"(?m)^UFS INIT case=.*$", guest)
    assert host.endswith("MT6897 UFS INIT MODEL PASS cases=67\n")
    assert guest.endswith("MT6897 ARM64 MODEL PASS\n")
    assert trace.stat().st_size == 0
    report = dict(passed=True, cases_per_environment=len(rows), native_sanitizers=["ASan", "UBSan"],
                  standalone_arm64_qemu=True, identical_results=True, model_only_build_guard=True,
                  virtual_ufs_accesses=0, production_provider_linked=False, physical_access=False)
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"MT6897 UFS initialization model PASS {len(rows)} cases each, native and ARM64 QEMU")


if __name__ == "__main__":
    main()
