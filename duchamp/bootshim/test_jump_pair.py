#!/usr/bin/env python3
"""Run the normal and intentional-return QEMU JUMP tests as one regression."""

import argparse
import shutil
import struct
import subprocess
import sys
from pathlib import Path


SEGMENT_TABLE = 0x2A8
RETURN_CHECKPOINT = 0x4455434851454D55
RETURN_RECORD_SYMBOL = "duchamp_bootshim_xnu_return_record"
RETURN_LOG_SYMBOL = "duchamp_bootshim_xnu_log"
RETURN_STUB_SYMBOL = "duchamp_xnu_return_stub"


def payload_facts(path):
    data = path.read_bytes()
    magic, version, segment_count = struct.unpack_from("<8sII", data, 0)
    if magic != b"SWEETXNU" or version != 1 or not 1 <= segment_count <= 32:
        raise SystemExit(f"invalid payload header: {path}")
    virt_base = struct.unpack_from("<Q", data, 0x10)[0]
    phys_base = struct.unpack_from("<Q", data, 0x38)[0]
    matches = []
    for index in range(segment_count):
        vmaddr, _vmsize, file_offset, file_size = struct.unpack_from(
            "<4Q", data, SEGMENT_TABLE + index * 32)
        start = file_offset
        stop = file_offset + file_size
        at = data.find(b"XNULDRST", start, stop)
        while at != -1:
            slot_va = vmaddr + at - file_offset
            matches.append(phys_base + slot_va - virt_base)
            at = data.find(b"XNULDRST", at + 8, stop)
    if len(matches) != 1:
        raise SystemExit(
            f"payload must contain exactly one return slot, found {len(matches)}")
    return matches[0], (phys_base - virt_base) & ((1 << 64) - 1)


def elf_symbol(path, name):
    llvm_nm = shutil.which("llvm-nm")
    if not llvm_nm:
        raise SystemExit("llvm-nm is not installed")
    output = subprocess.check_output(
        [llvm_nm, "-n", str(path)], text=True, errors="replace")
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[-1] == name:
            return int(fields[0], 16)
    raise SystemExit(f"missing ELF symbol {name}: {path}")


def run(test_qemu, common, image, elf, pattern, checkpoint, no_return):
    stub_pa = common["load_base"] + elf_symbol(elf, RETURN_STUB_SYMBOL)
    record_pa = common["load_base"] + elf_symbol(elf, RETURN_RECORD_SYMBOL)
    log_pa = common["load_base"] + elf_symbol(elf, RETURN_LOG_SYMBOL)
    command = [
        sys.executable, str(test_qemu),
        "--image", str(image),
        "--pattern", pattern,
        "--memory", common["memory"],
        "--wait", str(common["wait"]),
        "--dtb", str(common["dtb"]),
        "--slot-pa", hex(common["slot_pa"]),
        "--expect-slot-stub", hex(stub_pa),
        "--expect-slot-checkpoint", hex(checkpoint),
        "--expect-slot-delta", hex(common["delta"]),
        "--return-record-pa", hex(record_pa),
        "--return-log-pa", hex(log_pa),
    ]
    if no_return:
        command.append("--expect-no-return")
    else:
        command.extend(["--expect-return-reason", "1"])
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--dtb", type=Path, required=True)
    parser.add_argument("--normal-image", type=Path, required=True)
    parser.add_argument("--normal-elf", type=Path, required=True)
    parser.add_argument("--return-image", type=Path, required=True)
    parser.add_argument("--return-elf", type=Path, required=True)
    parser.add_argument("--memory", default="8G")
    parser.add_argument("--wait", type=float, default=2.0)
    parser.add_argument("--load-base", type=lambda value: int(value, 0),
                        default=0x40200000)
    args = parser.parse_args()
    paths = (args.payload, args.dtb, args.normal_image, args.normal_elf,
             args.return_image, args.return_elf)
    for path in paths:
        if not path.is_file():
            parser.error(f"missing file: {path}")
    slot_pa, delta = payload_facts(args.payload)
    common = {
        "dtb": args.dtb.resolve(),
        "memory": args.memory,
        "wait": args.wait,
        "load_base": args.load_base,
        "slot_pa": slot_pa,
        "delta": delta,
    }
    test_qemu = Path(__file__).with_name("test_qemu.py")
    print(f"jump-pair: normal slot={slot_pa:#x} delta={delta:#x}", flush=True)
    run(test_qemu, common, args.normal_image.resolve(),
        args.normal_elf.resolve(), "xnu", 0, True)
    print("jump-pair: intentional early return", flush=True)
    run(test_qemu, common, args.return_image.resolve(),
        args.return_elf.resolve(), "early-return", RETURN_CHECKPOINT, False)
    print("bootshim-qemu-jump-pair: PASS")


if __name__ == "__main__":
    main()
