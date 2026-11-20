#!/usr/bin/env python3
"""Replay the pinned LK decoder with input/output guard pages in QEMU only.

The firmware is an existing local input and is never changed or installed.
No phone transport, device MMIO or physical ownership claims are provided.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_MEM


LK_HASH = "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a"
IMAGE_HASH = "2be899ce4c76a740c3006089efd25e292b42b6e59bee10722610dd4203cb426b"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lk", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    lk, frame, image = (getattr(args, name).read_bytes() for name in ("lk", "frame", "image"))
    if digest(lk) != LK_HASH or digest(image) != IMAGE_HASH:
        raise ValueError("firmware or reference Image differs from the audited baseline")
    if len(image) != 57417168 or frame[:4] != bytes.fromhex("02214c18"):
        raise ValueError("unexpected candidate fixture")
    cursor, logical, blocks = 4, 0, []
    while cursor < len(frame):
        if len(frame) - cursor < 4 or len(blocks) >= 7:
            raise ValueError("invalid legacy LZ4 frame")
        size = struct.unpack_from("<I", frame, cursor)[0]
        cursor += 4
        if not 0 < size <= min(0x7fffffff, len(frame) - cursor):
            raise ValueError("invalid compressed block size")
        expanded = min(0x800000, len(image) - logical)
        blocks.append((cursor, size, expanded, logical))
        cursor += size
        logical += expanded
    if len(blocks) != 7 or logical != len(image):
        raise ValueError("unexpected fixture block count")
    for executable in ("clang", "ld.lld", "qemu-system-aarch64"):
        if shutil.which(executable) is None:
            raise ValueError("missing isolated-test dependency " + executable)
    out.mkdir(parents=True, exist_ok=True)
    sources = Path(__file__).resolve().parent.parent / "duchamp" / "tests"
    for name in ("lk_lz4_bounds.c", "lk_lz4_bounds.S", "lk_lz4_bounds.ld"):
        shutil.copyfile(sources / name, out / name)
    code = lk[0x200:0x200 + 0xf1c70]
    (out / "lk-code.bin").write_bytes(code)
    header = "struct fixture_block { uint64_t offset, compressed, expanded, logical; };\n"
    header += "static const struct fixture_block fixture_blocks[7] = {\n"
    header += "".join("    {%d,%d,%d,%d},\n" % row for row in blocks) + "};\n"
    (out / "fixture.h").write_text(header)
    commands = [
        ["clang", "--target=aarch64-none-elf", "-fuse-ld=lld", "-O2", "-ffreestanding",
         "-fno-builtin", "-fno-stack-protector", "-mgeneral-regs-only", "-nostdlib",
         "-Wl,-T,lk_lz4_bounds.ld", "-I.", "lk_lz4_bounds.S", "lk_lz4_bounds.c",
         "-o", "lk-lz4-bounds.elf"],
        ["qemu-system-aarch64", "-machine", "virt,gic-version=3", "-cpu", "cortex-a76",
         "-m", "1G", "-display", "none", "-serial", "none", "-monitor", "none",
         "-no-reboot", "-semihosting-config", "enable=on,target=native",
         "-kernel", str(out / "lk-lz4-bounds.elf"),
         "-device", f"loader,file={args.frame.resolve()},addr=0x60000000,force-raw=on",
         "-device", f"loader,file={args.image.resolve()},addr=0x68000000,force-raw=on"],
    ]
    report = {"scope": "isolated-QEMU-decoder-regression", "physical_execution_authorized": False,
              "phone_operations": [], "firmware_sha256": digest(lk), "frame_sha256": digest(frame),
              "image_sha256": digest(image), "commands": [], "passed": False}
    for index, cmd in enumerate(commands):
        started = time.monotonic()
        try:
            result = subprocess.run(cmd, cwd=out, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=55)
            stdout, rc = result.stdout, result.returncode
        except subprocess.TimeoutExpired as error:
            stdout, rc = (error.stdout or b"") + b"\nTIMEOUT\n", 124
        log = out / ("compile.log" if index == 0 else "qemu.log")
        log.write_bytes(stdout)
        report["commands"].append({"argv": cmd, "cwd": str(out), "exit_code": rc,
                                   "seconds": time.monotonic() - started,
                                   "log": str(log), "log_sha256": digest(stdout)})
        (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
        if rc:
            print(stdout.decode(errors="replace"))
            raise ValueError(f"isolated test command failed with exit {rc}")
    log = (out / "qemu.log").read_text()
    cases = [int(n) for n in re.findall(r"PASS case=(\d+)", log)]
    if cases != list(range(1, 14)) or "PASS 13/13" not in log:
        raise ValueError("missing or repeated regression case")
    match = re.search(r"FAULT pc=(0x[0-9a-f]+) far=(0x[0-9a-f]+) esr=(0x[0-9a-f]+)", log)
    if match is None:
        raise ValueError("missing deliberate guard-fault record")
    pc, far, esr = (int(value, 16) for value in match.groups())
    registers = {int(n): int(value, 16) for n, value in re.findall(r" x(\d+)=(0x[0-9a-f]+)", log)}
    offset = pc - 0x50700000 + 0x200
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    instruction = next(md.disasm(lk[offset:offset + 4], pc))
    operand = next(op for op in instruction.operands if op.type == ARM64_OP_MEM)
    base_name = instruction.reg_name(operand.mem.base)
    if not base_name.startswith("x") or operand.mem.index:
        raise ValueError("guard instruction requires manual address analysis")
    effective = registers[int(base_name[1:])] + operand.mem.disp
    fault = {"pc": pc, "lk_file_offset": offset, "far": far, "esr": esr,
             "instruction": instruction.mnemonic + " " + instruction.op_str,
             "effective_address": effective, "registers": registers,
             "meaning": "declared capacity exceeds mapped logical-only output fixture"}
    if (offset != 0x5931c or instruction.mnemonic != "str" or
            instruction.op_str != "x21, [x6]" or effective != 0x45fffffc or
            far != 0x46000000 or not esr & 0x40):
        raise ValueError("guard fault is not the expected output write")
    fault.update(access_bytes=8, access_end_exclusive=effective + 8,
                 bytes_after_logical_end=effective + 8 - far,
                 observed_tail_bytes_hex="00000000")
    if "TAIL four zero bytes from wide match copy verified" not in log:
        raise ValueError("tail extent or contents were not verified")
    # Check that the test links the original firmware payload without editing it.
    elf = (out / "lk-lz4-bounds.elf").read_bytes()
    phoff = struct.unpack_from("<Q", elf, 32)[0]
    stride, count = struct.unpack_from("<HH", elf, 54)
    found = []
    for index in range(count):
        kind, _, pos, va, _, size, _, _ = struct.unpack_from("<IIQQQQQQ", elf, phoff + index * stride)
        if kind == 1 and va == 0x50700000:
            if elf[pos:pos + size] != code:
                raise ValueError("test firmware copy changed")
            found.append(size)
    if found != [len(code)]:
        raise ValueError("test firmware segment missing or duplicated")
    report.update(passed=True, cases=13, guard_fault=fault, copied_firmware_bytes=len(code),
                  elf_sha256=digest(elf), source_files=[
                      {"path": str((sources / name).resolve()), "sha256": digest((sources / name).read_bytes())}
                      for name in ("lk_lz4_bounds.c", "lk_lz4_bounds.S", "lk_lz4_bounds.ld")])
    (out / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(log)
    print(json.dumps({"passed": True, "cases": 13, "guard_instruction": fault["instruction"],
                      "lk_file_offset": hex(offset), "effective_address": hex(effective),
                      "physical_execution_authorized": False}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, StopIteration, struct.error) as error:
        sys.exit(str(error))
