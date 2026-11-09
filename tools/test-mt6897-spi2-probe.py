#!/usr/bin/env python3
"""Exercise the one-shot SPI2 diagnostic on the host and in ARM64 QEMU."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory


def run(args, timeout):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    print(result.stdout, end="")
    if result.returncode:
        raise RuntimeError(result.stderr or f"test command exited {result.returncode}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, help="use the first DOWN frame from android-verified.json")
    args = parser.parse_args()
    drivers = Path(__file__).resolve().parents[1] / "duchamp/drivers"
    sources = [drivers / name for name in (
        "duchamp_ft3683g.c", "mt6897_spi2_probe.c", "test_mt6897_spi2_probe.c",
    )]
    common = ["clang", "-std=c11", "-Wall", "-Wextra", "-Werror"]
    with TemporaryDirectory(prefix="mt6897-spi2-probe-") as scratch:
        out = Path(scratch)
        if args.capture:
            first = json.loads(args.capture.read_text())["captured"][0]
            frame = bytes.fromhex(first["wire"])
            x, y = first["raw_x"], first["raw_y"]
            if (len(frame) != 100 or first["phase"] != "DOWN" or
                    not (type(x) is int and type(y) is int and 0 <= x < 19520 and 0 <= y < 43392)):
                parser.error("expected one 100-byte DOWN frame with native coordinates")
            (out / "spi2-capture.h").write_text(
                "static const uint8_t wire[DFT_WIRE_BYTES] = { "
                + ", ".join(hex(byte) for byte in frame) + " };\n"
                + f"enum {{ EXPECTED_X = {x}, EXPECTED_Y = {y} }};\n",
                encoding="ascii",
            )
            common.extend(["-DMT6897_SPI2_CAPTURE", "-I", out])
        native = out / "probe-native"
        run([*common, "-O1", "-g", "-fsanitize=address,undefined",
             "-fno-sanitize-recover=all", *sources, "-o", native], 60)
        native_output = run([native], 20)
        linker = out / "model.ld"
        linker.write_text(
            "ENTRY(_start)\nSECTIONS {\n"
            " . = 0x40200000; .text : { *(.text.boot) *(.text*) }\n"
            " .rodata : { *(.rodata*) } .data : { *(.data*) } . = ALIGN(4096);\n"
            " .bss (NOLOAD) : { _bss_start = .; *(.bss*) *(COMMON)\n"
            " . = ALIGN(16); _bss_end = .; } . += 0x40000; _stack_top = .;\n}\n",
            encoding="ascii",
        )
        elf = out / "probe-qemu.elf"
        run([*common, "--target=aarch64-none-elf", "-O2", "-ffreestanding", "-fno-builtin",
             "-mgeneral-regs-only", "-mstrict-align", "-DMT6897_MODEL_FREESTANDING", "-nostdlib",
             "-fuse-ld=lld", f"-Wl,-T,{linker}", *sources,
             drivers / "test_mt6897_model_start.S", drivers / "test_mt6897_model_runtime.c",
             "-o", elf], 60)
        arm_output = run(["qemu-system-aarch64", "-M", "virt,gic-version=3", "-cpu", "cortex-a76",
                          "-m", "64M", "-nographic", "-monitor", "none", "-nic", "none",
                          "-semihosting-config", "enable=on,target=native", "-kernel", elf], 20)
    marker = r"(?m)^(\d+) SPI2 one-shot DMA scenarios passed\s*$"
    native_count, arm_count = re.findall(marker, native_output), re.findall(marker, arm_output)
    if not native_count or native_count != arm_count or "MT6897 ARM64 MODEL PASS" not in arm_output:
        raise RuntimeError("host and QEMU did not report matching SPI2 success")


if __name__ == "__main__":
    main()
