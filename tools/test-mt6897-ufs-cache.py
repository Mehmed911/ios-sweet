#!/usr/bin/env python3
"""Verify the lease-bound MT6897 non-coherent cache contract locally.

The test executes native sanitizer checks, verifies the freestanding ARM64
imports, and runs the same policy model on an actual ARM64 CPU under QEMU.
It does not access a phone, peripheral, partition, cache controller or DMA
engine.  Existing output directories are never overwritten.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


REPORT_VERSION = 1
SUMMARY = re.compile(
    r"(?m)^(\d+) MT6897 UFS noncoherent-cache checks passed; "
    r"current_callbacks=(\d+) model_handoffs=(\d+)\s*$"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, commands, directory, name, env=None):
    commands.append({"name": name, "command": [str(item) for item in command]})
    result = subprocess.run(
        command,
        cwd=directory,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    if result.returncode != 0:
        raise ValueError(
            name + " failed with exit " + str(result.returncode) + "\n" +
            result.stdout[-8000:]
        )
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    drivers = repo / "duchamp/drivers"
    gate_source = drivers / "mt6897_ufs_gate.c"
    gate_header = drivers / "mt6897_ufs_gate.h"
    cache_source = drivers / "mt6897_ufs_cache.c"
    cache_header = drivers / "mt6897_ufs_cache.h"
    test_source = drivers / "test_mt6897_ufs_cache.c"
    concurrency_source = drivers / "test_mt6897_ufs_cache_concurrency.c"
    model_runtime = drivers / "test_mt6897_model_runtime.c"
    model_start = drivers / "test_mt6897_model_start.S"
    script = Path(__file__).resolve()
    sources = (
        gate_source,
        gate_header,
        cache_source,
        cache_header,
        test_source,
        concurrency_source,
        model_runtime,
        model_start,
        script,
    )
    for source in sources:
        require(source.is_file(), "missing source: " + str(source))

    clang = shutil.which("clang")
    llvm_nm = shutil.which("llvm-nm")
    qemu = shutil.which("qemu-system-aarch64")
    require(clang is not None, "clang is required")
    require(llvm_nm is not None, "llvm-nm is required")
    require(qemu is not None, "qemu-system-aarch64 is required")

    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix="." + output.name + ".tmp-", dir=str(output.parent)
    ))
    published = False
    source_before = {
        str(path.relative_to(repo)).replace("\\", "/"): sha256(path)
        for path in sources
    }
    commands = []
    try:
        native = temporary / "mt6897-ufs-cache-test"
        native_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            str(gate_source),
            str(cache_source),
            str(test_source),
            "-o",
            str(native),
        ]
        run(native_compile, commands, temporary, "native-compile")
        sanitizer_env = os.environ.copy()
        sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
        sanitizer_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        native_output = run(
            [str(native)], commands, temporary, "native-test", sanitizer_env
        )
        native_match = SUMMARY.search(native_output)
        require(native_match is not None, "unexpected native test summary")
        native_checks = int(native_match.group(1))
        current_callbacks = int(native_match.group(2))
        model_handoffs = int(native_match.group(3))
        require(native_checks > 0, "native test reported no checks")
        require(current_callbacks == 0,
                "current Duchamp evidence reached a cache callback")
        require(model_handoffs == 6,
                "synthetic model did not cover both handoffs in 3 directions")

        concurrency = temporary / "mt6897-ufs-cache-concurrency-test"
        concurrency_compile = [
            clang,
            "-std=c11",
            "-O1",
            "-g",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
            "-pthread",
            "-DMT6897_UFS_CACHE_TEST_HOOKS",
            str(gate_source),
            str(cache_source),
            str(concurrency_source),
            "-o",
            str(concurrency),
        ]
        run(concurrency_compile, commands, temporary,
            "concurrency-compile")
        concurrency_output = run(
            [str(concurrency)], commands, temporary, "concurrency-test",
            sanitizer_env,
        )
        concurrency_match = re.search(
            r"(?m)^(\d+) MT6897 UFS concurrent cache checks passed; "
            r"fault_before_cache_callback=1 range_callbacks=0\s*$",
            concurrency_output,
        )
        require(concurrency_match is not None,
                "unexpected concurrent cache-test summary")
        concurrency_checks = int(concurrency_match.group(1))
        require(concurrency_checks > 0,
                "concurrent cache test reported no checks")

        arm64_object = temporary / "mt6897_ufs_cache.arm64.o"
        arm64_compile = [
            clang,
            "-target", "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-c",
            str(cache_source),
            "-o",
            str(arm64_object),
        ]
        run(arm64_compile, commands, temporary, "arm64-object-compile")
        imports_text = run(
            [llvm_nm, "--undefined-only", str(arm64_object)],
            commands,
            temporary,
            "arm64-object-imports",
        )
        imports = sorted(
            line.split()[-1] for line in imports_text.splitlines() if line.split()
        )
        require(imports == [
            "mt6897_ufs_gate_fault",
            "mt6897_ufs_gate_lease_check",
        ], "unexpected cache-contract imports: " + ", ".join(imports))

        linker = temporary / "model.ld"
        linker.write_text(
            "ENTRY(_start)\nSECTIONS { . = 0x40200000;\n"
            " .text : { *(.text.boot) *(.text*) }\n"
            " .rodata : { *(.rodata*) }\n"
            " .data : { *(.data*) }\n . = ALIGN(4096);\n"
            " .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON) "
            ". = ALIGN(16); _bss_end = .; }\n"
            " . += 0x40000; _stack_top = .;\n}\n",
            encoding="utf-8",
        )
        arm64_elf = temporary / "mt6897-ufs-cache-model.arm64.elf"
        arm64_link = [
            clang,
            "-target", "aarch64-none-elf",
            "-std=c11",
            "-O2",
            "-ffreestanding",
            "-fno-builtin",
            "-mgeneral-regs-only",
            "-mstrict-align",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-DMT6897_MODEL_FREESTANDING",
            "-nostdlib",
            "-fuse-ld=lld",
            "-Wl,-T," + str(linker),
            str(model_start),
            str(model_runtime),
            str(gate_source),
            str(cache_source),
            str(test_source),
            "-o",
            str(arm64_elf),
        ]
        run(arm64_link, commands, temporary, "arm64-model-link")
        arm64_output = run([
            qemu,
            "-M", "virt",
            "-cpu", "cortex-a76",
            "-smp", "1",
            "-m", "64M",
            "-nographic",
            "-monitor", "none",
            "-serial", "stdio",
            "-nic", "none",
            "-semihosting-config", "enable=on,target=native",
            "-kernel", str(arm64_elf),
        ], commands, temporary, "arm64-model-test")
        arm64_match = SUMMARY.search(arm64_output)
        require(arm64_match is not None, "unexpected ARM64 model summary")
        require(tuple(arm64_match.groups()) == tuple(native_match.groups()),
                "ARM64 model did not reproduce native checks")
        require("MT6897 ARM64 MODEL PASS" in arm64_output,
                "ARM64 model did not report PASS")

        source_after = {
            str(path.relative_to(repo)).replace("\\", "/"): sha256(path)
            for path in sources
        }
        require(source_after == source_before, "sources changed during test")

        result = {
            "report_version": REPORT_VERSION,
            "passed": True,
            "contract_version": 1,
            "native": {
                "checks": native_checks,
                "sanitizers": "ASan + UBSan",
                "current_duchamp_callbacks": current_callbacks,
                "synthetic_model_handoffs": model_handoffs,
            },
            "concurrency": {
                "checks": concurrency_checks,
                "sanitizers": "ASan + UBSan",
                "fault_before_cache_callback": True,
                "range_callbacks": 0,
            },
            "arm64_object": {
                "freestanding_compile": True,
                "undefined_imports": imports,
                "sha256": sha256(arm64_object),
            },
            "arm64_qemu_model": {
                "passed": True,
                "checks": int(arm64_match.group(1)),
                "same_output_as_native": True,
                "elf_sha256": sha256(arm64_elf),
                "scope": (
                    "actual ARM64 CPU execution under QEMU virt with "
                    "MMU/cache off and no MediaTek peripheral emulation"
                ),
            },
            "contract": {
                "default_closed": True,
                "lease_checked_at_bind_and_every_transition": True,
                "exclusive_whole_cache_lines_required": True,
                "cpu_aliases_forbidden": True,
                "device_handoff": "clean-to-PoC then barrier",
                "cpu_handoff_to_device_direction": "barriers only",
                "cpu_handoff_from_or_bidirectional": (
                    "barrier, clean+invalidate-to-PoC, barrier"
                ),
                "runtime_callback_failure": "terminal fail-closed",
                "physical_backend": "disabled",
            },
            "current_duchamp_evidence": {
                "activation_lease_available": False,
                "cache_callbacks": current_callbacks,
                "physical_cache_maintenance_authorized": False,
            },
            "source_sha256": source_before,
            "sources_unchanged": True,
            "safety": {
                "local_files_only": True,
                "phone_access": False,
                "adb_access": False,
                "fastboot_access": False,
                "network_access": False,
                "mmio_access": False,
                "smc_execution": False,
                "dma_access": False,
                "cache_instruction_execution_by_contract": False,
                "partition_access": False,
            },
            "scope": (
                "native sanitizers, freestanding ARM64 compilation and an "
                "ARM64 QEMU callback/state model only; no physical UFS "
                "authorization"
            ),
        }
        (temporary / "commands.json").write_text(
            json.dumps(commands, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (temporary / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        require(not output.exists(), "preserve existing output")
        temporary.rename(output)
        published = True
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        if not published and temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
