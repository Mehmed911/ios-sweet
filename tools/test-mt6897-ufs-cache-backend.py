#!/usr/bin/env python3
"""Verify the XNU/generic-ARM64 MT6897 UFS cache callback backend locally.

The host and freestanding ARM64 models replace the cache primitives with
private test hooks.  A separate object audit proves that the production object
imports only XNU's clean/flush-to-PoC primitives and contains the pinned
barriers.  No phone, peripheral, MMIO, DMA, firmware or partition is accessed.
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


SUMMARY = re.compile(
    r"(?m)^(\d+) MT6897 XNU cache-backend checks passed; "
    r"clean=1 flush=1 barriers=3 fail_closed=1\s*$"
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
    xnu = repo / "duchamp/xnu"
    source = xnu / "mt6897_ufs_cache_backend.c"
    header = xnu / "mt6897_ufs_cache_backend.h"
    test = xnu / "test_mt6897_ufs_cache_backend.c"
    cache_header = drivers / "mt6897_ufs_cache.h"
    gate_header = drivers / "mt6897_ufs_gate.h"
    model_runtime = drivers / "test_mt6897_model_runtime.c"
    model_start = drivers / "test_mt6897_model_start.S"
    script = Path(__file__).resolve()
    sources = (
        source, header, test, cache_header, gate_header,
        model_runtime, model_start, script,
    )
    for item in sources:
        require(item.is_file(), "missing source: " + str(item))

    clang = shutil.which("clang")
    llvm_nm = shutil.which("llvm-nm")
    llvm_objdump = shutil.which("llvm-objdump")
    qemu = shutil.which("qemu-system-aarch64")
    require(clang is not None, "clang is required")
    require(llvm_nm is not None, "llvm-nm is required")
    require(llvm_objdump is not None, "llvm-objdump is required")
    require(qemu is not None, "qemu-system-aarch64 is required")

    output = args.output.resolve()
    require(not output.exists(), "preserve existing output: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix="." + output.name + ".tmp-", dir=str(output.parent)
    ))
    published = False
    commands = []
    before = {
        str(item.relative_to(repo)).replace("\\", "/"): sha256(item)
        for item in sources
    }
    include = ["-I", str(xnu), "-I", str(drivers)]
    try:
        native = temporary / "mt6897-ufs-cache-backend-test"
        native_compile = [
            clang, "-std=c11", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer", "-DMT6897_UFS_XNU_CACHE_BACKEND_TEST",
            *include, str(source), str(test), "-o", str(native),
        ]
        run(native_compile, commands, temporary, "native-compile")
        sanitizer_env = os.environ.copy()
        sanitizer_env["ASAN_OPTIONS"] = "halt_on_error=1"
        sanitizer_env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
        native_output = run(
            [str(native)], commands, temporary, "native-test", sanitizer_env
        )
        native_match = SUMMARY.search(native_output)
        require(native_match is not None, "unexpected native summary")
        native_checks = int(native_match.group(1))
        require(native_checks > 0, "native model reported no checks")

        production_object = temporary / "mt6897_ufs_cache_backend.arm64.o"
        production_compile = [
            clang, "-target", "aarch64-none-elf", "-std=c11", "-O2",
            "-ffreestanding", "-fno-builtin", "-mgeneral-regs-only",
            "-Wall", "-Wextra", "-Werror", *include, "-c", str(source),
            "-o", str(production_object),
        ]
        run(production_compile, commands, temporary, "production-object-compile")
        imports_text = run(
            [llvm_nm, "--undefined-only", str(production_object)], commands,
            temporary, "production-object-imports"
        )
        imports = sorted(
            line.split()[-1] for line in imports_text.splitlines() if line.split()
        )
        require(imports == [
            "CleanPoC_DcacheRegion", "FlushPoC_DcacheRegion"
        ], "unexpected production imports: " + ", ".join(imports))
        disassembly = run(
            [llvm_objdump, "-d", str(production_object)], commands,
            temporary, "production-object-disassembly"
        )
        require(re.search(r"\bdsb\s+sy\b", disassembly) is not None,
                "production backend lacks dsb sy")
        require(re.search(r"\bisb\b", disassembly) is not None,
                "production backend lacks isb")

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
        arm64_elf = temporary / "mt6897-ufs-cache-backend-model.arm64.elf"
        arm64_link = [
            clang, "-target", "aarch64-none-elf", "-std=c11", "-O2",
            "-ffreestanding", "-fno-builtin", "-mgeneral-regs-only",
            "-mstrict-align", "-Wall", "-Wextra", "-Werror",
            "-DMT6897_MODEL_FREESTANDING",
            "-DMT6897_UFS_XNU_CACHE_BACKEND_TEST", "-nostdlib",
            "-fuse-ld=lld", "-Wl,-T," + str(linker), *include,
            str(model_start), str(model_runtime), str(source), str(test),
            "-o", str(arm64_elf),
        ]
        run(arm64_link, commands, temporary, "arm64-model-link")
        arm64_output = run([
            qemu, "-M", "virt", "-cpu", "cortex-a76", "-smp", "1",
            "-m", "64M", "-nographic", "-monitor", "none",
            "-serial", "stdio", "-nic", "none",
            "-semihosting-config", "enable=on,target=native",
            "-kernel", str(arm64_elf),
        ], commands, temporary, "arm64-model-test")
        arm64_match = SUMMARY.search(arm64_output)
        require(arm64_match is not None, "unexpected ARM64 model summary")
        require(int(arm64_match.group(1)) == native_checks,
                "ARM64 and native check counts differ")
        require("MT6897 ARM64 MODEL PASS" in arm64_output,
                "ARM64 model did not report PASS")

        after = {
            str(item.relative_to(repo)).replace("\\", "/"): sha256(item)
            for item in sources
        }
        require(after == before, "sources changed during test")
        result = {
            "report_version": 1,
            "passed": True,
            "backend_version": 1,
            "native": {
                "checks": native_checks,
                "sanitizers": "ASan + UBSan",
                "private_test_hooks": True,
            },
            "production_arm64_object": {
                "sha256": sha256(production_object),
                "undefined_imports": imports,
                "dsb_sy_present": True,
                "isb_present": True,
            },
            "arm64_qemu_model": {
                "passed": True,
                "checks": int(arm64_match.group(1)),
                "same_checks_as_native": True,
                "elf_sha256": sha256(arm64_elf),
            },
            "contract": {
                "exact_receipt_pinned": True,
                "clean_primitive": "CleanPoC_DcacheRegion",
                "flush_primitive": "FlushPoC_DcacheRegion",
                "barrier": "dsb sy; isb after CPU handoff",
                "callback_error": "terminal backend fault",
                "default_activation": "none",
            },
            "source_sha256": before,
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
                "partition_access": False,
                "production_cache_primitive_executed": False,
            },
            "scope": (
                "native/ARM64 callback model plus production object import and "
                "instruction audit; full XNU QEMU execution is a separate gate"
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
