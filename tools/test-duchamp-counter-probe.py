#!/usr/bin/env python3
"""Test the bounded counter probe natively and with real QEMU sysreg reads."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    repo = Path(__file__).resolve().parent.parent
    drivers = repo / "duchamp" / "drivers"
    test = drivers / "test_duchamp_counter_probe.c"
    header = drivers / "duchamp_counter_probe.h"
    start = drivers / "test_mt6897_model_start.S"
    runtime = drivers / "test_mt6897_model_runtime.c"
    paths = (test, header, start, runtime, Path(__file__).resolve())
    before = {str(path.relative_to(repo)): digest(path) for path in paths}
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        (output / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        try:
            return subprocess.run(
                command, check=True, capture_output=True, text=True, **kwargs)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            stdout = error.stdout.decode(errors="replace") \
                if isinstance(error.stdout, bytes) else error.stdout or ""
            stderr = error.stderr.decode(errors="replace") \
                if isinstance(error.stderr, bytes) else error.stderr or ""
            (output / "failure.log").write_text(
                stdout + stderr, encoding="utf-8")
            raise

    native = output / "native"
    native_run = run([
        "clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O1", "-g",
        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
        str(test), "-o", str(native),
    ])
    if native_run.stdout or native_run.stderr:
        raise ValueError("native counter-probe build emitted output")
    native_result = run([str(native)])
    (output / "native.log").write_text(
        native_result.stdout + native_result.stderr, encoding="utf-8")
    native_match = re.fullmatch(
        r"(\d+) counter probe checks passed\n", native_result.stdout)
    if not native_match or native_result.stderr:
        raise ValueError("native counter-probe checks failed")

    linker = output / "test.ld"
    linker.write_text(
        "ENTRY(_start)\nSECTIONS { . = 0x40200000; "
        ".text : { *(.text.boot) *(.text*) } .rodata : { *(.rodata*) } "
        ".data : { *(.data*) } . = ALIGN(4096); .bss (NOLOAD) : { "
        "_bss_start = .; *(.bss*) *(COMMON) . = ALIGN(16); _bss_end = .; } "
        ". += 0x40000; _stack_top = .; }\n",
        encoding="utf-8",
    )
    elf = output / "counter-probe.elf"
    arm_build = run([
        "clang", "-target", "aarch64-none-elf", "-std=c11", "-O2",
        "-ffreestanding", "-fno-builtin", "-mgeneral-regs-only",
        "-mstrict-align", "-Wall", "-Wextra", "-Werror",
        "-DMT6897_MODEL_FREESTANDING", "-DDUCHAMP_COUNTER_ARCH_READS",
        "-nostdlib", "-fuse-ld=lld", "-Wl,-T," + str(linker),
        str(test), str(start), str(runtime), "-o", str(elf),
    ])
    if arm_build.stdout or arm_build.stderr:
        raise ValueError("AArch64 counter-probe build emitted output")
    arm = run([
        "qemu-system-aarch64", "-M", "virt,gic-version=3", "-cpu",
        "cortex-a76", "-m", "64M", "-nographic", "-monitor", "none",
        "-nic", "none", "-semihosting-config", "enable=on,target=native",
        "-kernel", str(elf),
    ], timeout=30)
    (output / "qemu.log").write_text(
        arm.stdout + arm.stderr, encoding="utf-8")
    arm_match = re.search(r"(\d+) counter probe checks passed\n", arm.stdout)
    if not arm_match or "MT6897 ARM64 MODEL PASS" not in arm.stdout:
        raise ValueError("AArch64 counter-probe execution failed")
    if int(arm_match.group(1)) != int(native_match.group(1)) + 3:
        raise ValueError("architected register checks did not execute")
    after = {str(path.relative_to(repo)): digest(path) for path in paths}
    if before != after:
        raise ValueError("counter-probe sources changed during test")
    report = {
        "passed": True,
        "native_checks": int(native_match.group(1)),
        "arm64_checks": int(arm_match.group(1)),
        "architected_register_reads_executed": True,
        "qemu_cntfrq_hz": 62500000,
        "timer_register_writes": False,
        "gic_access": False,
        "smc_execution": False,
        "phone_access": False,
        "elf_sha256": digest(elf),
        "source_sha256": before,
        "scope": (
            "actual CNTFRQ_EL0/CNTVCT_EL0 reads on QEMU only; no phone, "
            "GIC, timer-register write, SMC or partition access"
        ),
    }
    (output / "result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
