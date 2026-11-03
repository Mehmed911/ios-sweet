#!/usr/bin/env python3
"""Verify the lease-bound MT6897 PA-to-DMA/bounce contract locally.

The test executes native sanitizer checks, a deterministic fault race and the
same routing model on an actual ARM64 CPU under QEMU.  All successful mappings
use private process/model RAM and synthetic leases.  It performs no phone,
MMIO, cache instruction, DMA or UFS command access and never overwrites an
existing output directory.
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
    r"(?m)^(\d+) MT6897 UFS DMA-route checks passed; "
    r"current_callbacks=(\d+) direct_mappings=(\d+) bounce_mappings=(\d+)\s*$"
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
    route_source = drivers / "mt6897_ufs_dma_route.c"
    route_header = drivers / "mt6897_ufs_dma_route.h"
    test_source = drivers / "test_mt6897_ufs_dma_route.c"
    concurrency_source = drivers / "test_mt6897_ufs_dma_route_concurrency.c"
    model_runtime = drivers / "test_mt6897_model_runtime.c"
    model_start = drivers / "test_mt6897_model_start.S"
    script = Path(__file__).resolve()
    sources = (
        gate_source,
        gate_header,
        route_source,
        route_header,
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
        native = temporary / "mt6897-ufs-dma-route-test"
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
            str(route_source),
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
        direct_mappings = int(native_match.group(3))
        bounce_mappings = int(native_match.group(4))
        require(native_checks > 0, "native test reported no checks")
        require(current_callbacks == 0,
                "current Duchamp evidence reached a route callback")
        require(direct_mappings == 3 and bounce_mappings == 3,
                "synthetic model did not cover both routes in 3 directions")

        concurrency = temporary / "mt6897-ufs-dma-route-concurrency-test"
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
            "-DMT6897_UFS_DMA_ROUTE_TEST_HOOKS",
            str(gate_source),
            str(route_source),
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
            r"(?m)^(\d+) MT6897 UFS concurrent DMA-route checks passed; "
            r"fault_before_route_callback=1 copy_callbacks=0\s*$",
            concurrency_output,
        )
        require(concurrency_match is not None,
                "unexpected concurrent DMA-route test summary")
        concurrency_checks = int(concurrency_match.group(1))
        require(concurrency_checks > 0,
                "concurrent DMA-route test reported no checks")

        arm64_object = temporary / "mt6897_ufs_dma_route.arm64.o"
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
            str(route_source),
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
        ], "unexpected DMA-route imports: " + ", ".join(imports))

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
        arm64_elf = temporary / "mt6897-ufs-dma-route-model.arm64.elf"
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
            str(route_source),
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
                "synthetic_direct_mappings": direct_mappings,
                "synthetic_bounce_mappings": bounce_mappings,
            },
            "concurrency": {
                "checks": concurrency_checks,
                "sanitizers": "ASan + UBSan",
                "fault_before_route_callback": True,
                "copy_callbacks": 0,
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
                "immutable_receipt_fingerprint": True,
                "direct_translation": "pinned affine PA-to-DMA window",
                "bounce_translation": "dedicated pinned pool",
                "cache_contract": "pinned identifier; executed separately",
                "physical_backend": "disabled",
            },
            "scope": {
                "phone_access": False,
                "mmio": False,
                "cache_instruction": False,
                "dma": False,
                "ufs_command": False,
                "successful_paths": "synthetic lease and private RAM only",
            },
            "source_sha256": source_before,
            "commands": commands,
        }
        (temporary / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.rename(output)
        published = True
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        if not published:
            shutil.rmtree(temporary, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit("DMA-route test failed: " + str(error))
