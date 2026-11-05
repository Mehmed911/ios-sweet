#!/usr/bin/env python3
"""Verify the complete QEMU-only LK RAM bootshim and optional boot wrapper."""

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

IMAGE_LOAD = 0x40200000
FDT_LOAD = 0x48000000
FDT_RESERVE = 0x200000
STAGING_BASE = 0x90000000
STAGING_CAPACITY = 0x20000000
XNU_BASE = 0x1C0000000
XNU_SIZE = 0x20000000
QEMU_RAM_BASE = 0x40000000
QEMU_RAM_SIZE = 0x200000000
BOOT_PAGE = 4096
BOOT_HEADER_SIZE = 1584
AVB_FOOTER_SIZE = 64
AVB_FOOTER_FORMAT = ">4sIIQQQ28s"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def receipt(data):
    value = 1469598103934665603
    for byte in data:
        value ^= byte
        value = value * 1099511628211 & 0xFFFFFFFFFFFFFFFF
    value ^= len(data)
    return value * 1099511628211 & 0xFFFFFFFFFFFFFFFF


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def u64(data, offset):
    return struct.unpack_from("<Q", data, offset)[0]


def overlap(first, first_size, second, second_size):
    return first_size > 0 and second_size > 0 and (
        first < second + second_size and second < first + first_size)


def checked_end(start, size, label):
    end = start + size
    require(end <= 0xFFFFFFFFFFFFFFFF, f"{label} overflows uint64")
    return end


def parse_payload(payload):
    require(len(payload) >= 0x2A8 and payload[:8] == b"SWEETXNU",
            "payload lacks a complete SWEETXNU header")
    version, segment_count = struct.unpack_from("<II", payload, 8)
    require(version == 1 and 1 <= segment_count <= 32,
            "payload version or segment count is invalid")
    table_end = 0x2A8 + segment_count * 32
    require(table_end <= len(payload), "payload segment table is truncated")
    (virt_base, entry_va, adt_offset, adt_size, kernel_end, phys_base,
     memory_size) = struct.unpack_from("<7Q", payload, 0x10)
    require(phys_base == XNU_BASE and memory_size == XNU_SIZE,
            "payload physical window does not match the bootshim")
    require((virt_base | phys_base | memory_size) & 0x3FFF == 0,
            "payload memory window is not 16 KiB aligned")
    require(virt_base <= entry_va < kernel_end and
            virt_base < kernel_end <= checked_end(
                virt_base, memory_size, "payload virtual window") and
            kernel_end & 0x3FFF == 0,
            "payload entry/kernel_end is outside the virtual window")
    require(0 < adt_size <= 0x200000 and adt_offset >= table_end and
            checked_end(adt_offset, adt_size, "payload ADT") <= len(payload),
            "payload ADT range is invalid")
    entry_mapped = False
    greatest_end = virt_base
    file_ranges = []
    virtual_ranges = []
    for index in range(segment_count):
        vmaddr, vmsize, file_offset, file_size = struct.unpack_from(
            "<4Q", payload, 0x2A8 + index * 32)
        require(vmsize > 0 and vmaddr & 0x3FFF == 0 and
                file_size <= vmsize,
                f"payload segment {index} sizes are invalid")
        vmend = checked_end(vmaddr, vmsize, f"payload segment {index} VA")
        file_end = checked_end(
            file_offset, file_size, f"payload segment {index} file")
        require(virt_base <= vmaddr < vmend <= kernel_end and
                file_offset >= table_end and file_end <= len(payload) and
                not overlap(file_offset, file_size, adt_offset, adt_size),
                f"payload segment {index} lies outside its window")
        for start, size in virtual_ranges:
            require(not overlap(vmaddr, vmsize, start, size),
                    f"payload segment {index} overlaps another VA range")
        for start, size in file_ranges:
            require(not overlap(file_offset, file_size, start, size),
                    f"payload segment {index} overlaps another file range")
        virtual_ranges.append((vmaddr, vmsize))
        if file_size:
            file_ranges.append((file_offset, file_size))
        entry_mapped |= vmaddr <= entry_va and entry_va + 4 <= vmaddr + file_size
        greatest_end = max(greatest_end, vmend)
    require(entry_mapped and entry_va & 3 == 0 and greatest_end == kernel_end,
            "payload entry/kernel extent is not fully mapped")
    adt = phys_base + kernel_end - virt_base
    boot_args = (checked_end(adt, adt_size, "materialized ADT") +
                 0x3FFF) & ~0x3FFF
    top = checked_end(boot_args, 0x4000, "boot arguments")
    require(top <= phys_base + memory_size,
            "materialized ADT/boot arguments exceed the XNU window")
    return {
        "segment_count": segment_count,
        "entry": phys_base + entry_va - virt_base,
        "boot_args": boot_args,
        "phys_base": phys_base,
        "memory_size": memory_size,
    }


def read_symbols(elf):
    completed = subprocess.run(
        ["llvm-nm", "-n", str(elf)], check=True, capture_output=True,
        text=True)
    result = {}
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                result[fields[2]] = int(fields[0], 16)
            except ValueError:
                pass
    return result


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def verify_boot_wrapper(boot_path, stock_path, image):
    boot = boot_path.read_bytes()
    stock = stock_path.read_bytes()
    require(len(boot) == len(stock), "boot wrapper changed partition size")
    require(boot[:8] == b"ANDROID!", "boot wrapper lacks ANDROID! magic")
    require(u32(boot, 20) == BOOT_HEADER_SIZE and u32(boot, 40) == 4,
            "boot wrapper is not header v4")
    require(u32(boot, 12) == 0 and u32(boot, 1580) == 0,
            "boot wrapper unexpectedly contains a ramdisk or signature")
    kernel_size = u32(boot, 8)
    require(0 < kernel_size <= len(boot) - BOOT_PAGE,
            "boot wrapper kernel size is outside the image")
    kernel = boot[BOOT_PAGE:BOOT_PAGE + kernel_size]
    if kernel[:4] == bytes.fromhex("02214c18"):
        lz4 = shutil.which("lz4")
        require(lz4 is not None, "lz4 is required to verify the boot wrapper")
        completed = subprocess.run(
            [lz4, "-d", "-c"], input=kernel, capture_output=True)
        require(completed.returncode == 0,
                f"cannot decompress boot kernel: {completed.stderr!r}")
        unpacked = completed.stdout
        kernel_format = "lz4-legacy"
    else:
        unpacked = kernel
        kernel_format = "raw"
    require(unpacked == image,
            "boot wrapper kernel does not reproduce the verified Image")

    stock_header = bytearray(stock[:BOOT_HEADER_SIZE])
    boot_header = bytearray(boot[:BOOT_HEADER_SIZE])
    struct.pack_into("<I", stock_header, 8, 0)
    struct.pack_into("<I", boot_header, 8, 0)
    require(boot_header == stock_header,
            "boot metadata changed outside kernel_size")
    require(not any(boot[BOOT_HEADER_SIZE:BOOT_PAGE]),
            "boot header page padding is not zero")

    footer = struct.unpack(AVB_FOOTER_FORMAT, stock[-AVB_FOOTER_SIZE:])
    magic, major, minor, original_size, vbmeta_offset, vbmeta_size, _ = footer
    require(magic == b"AVBf" and major == 1 and minor == 0,
            "stock boot lacks the expected AVB footer")
    require(boot[-AVB_FOOTER_SIZE:] == stock[-AVB_FOOTER_SIZE:],
            "AVB footer was not preserved byte-for-byte")
    require(vbmeta_offset == original_size and vbmeta_size > 0 and
            vbmeta_offset + vbmeta_size <= len(boot) - AVB_FOOTER_SIZE,
            "stock AVB placement is invalid")
    require(boot[vbmeta_offset:vbmeta_offset + vbmeta_size] ==
            stock[vbmeta_offset:vbmeta_offset + vbmeta_size],
            "stock vbmeta was not preserved byte-for-byte")
    payload_end = (BOOT_PAGE + kernel_size + BOOT_PAGE - 1) & ~(BOOT_PAGE - 1)
    require(payload_end <= original_size,
            "boot kernel overlaps preserved AVB metadata")
    require(not any(boot[payload_end:original_size]),
            "pre-vbmeta padding contains unexpected bytes")
    return {
        "path": str(boot_path.resolve()),
        "sha256": sha256(boot),
        "size": len(boot),
        "kernel_size": kernel_size,
        "kernel_format": kernel_format,
        "vbmeta_offset": vbmeta_offset,
        "vbmeta_size": vbmeta_size,
        "avb_payload_hash": "expected-mismatch",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--capsule", type=Path, required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--fdt", type=Path, required=True)
    parser.add_argument("--boot-image", type=Path)
    parser.add_argument("--stock-boot", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    require((args.boot_image is None) == (args.stock_boot is None),
            "--boot-image and --stock-boot must be supplied together")

    elf = args.elf.resolve()
    image = args.image.read_bytes()
    capsule = args.capsule.read_bytes()
    payload = args.payload.read_bytes()
    fdt = args.fdt.read_bytes()
    require(len(image) >= 64 and image[56:60] == b"ARM\x64",
            "Image lacks the arm64 Linux header")
    require(u64(image, 16) == len(image),
            "Image header size does not equal the complete Image")
    require(u64(image, 24) == 0xA,
            "Image flags do not describe little-endian 4 KiB pages")

    symbols = read_symbols(elf)
    required = ("_head", "_bss_start", "_bss_end", "_stack_top",
                "duchamp_lk_ram_capsule_start",
                "duchamp_lk_ram_capsule_end", "_end",
                "duchamp_lk_ram_boot_report")
    missing = [name for name in required if name not in symbols]
    require(not missing, f"ELF is missing symbols: {missing}")
    require("duchamp_enter_xnu" not in symbols,
            "QEMU-only image unexpectedly contains the XNU branch helper")
    head = symbols["_head"]
    capsule_start = symbols["duchamp_lk_ram_capsule_start"]
    capsule_end = symbols["duchamp_lk_ram_capsule_end"]
    require(head == IMAGE_LOAD and symbols["_end"] - head == len(image),
            "ELF head/end do not match the binary Image")
    require(symbols["_bss_start"] <= symbols["_bss_end"] <=
            symbols["_stack_top"] <= capsule_start < capsule_end <=
            symbols["_end"], "ELF section ordering is unsafe")
    require(capsule_start % 16 == 0,
            "capsule is not 16-byte aligned")
    capsule_offset = capsule_start - head
    capsule_end_offset = capsule_end - head
    require(capsule_end - capsule_start == len(capsule) and
            image[capsule_offset:capsule_end_offset] == capsule,
            "ELF capsule section does not match payload.lkram")

    relocations = subprocess.run(
        ["llvm-readelf", "-r", str(elf)], check=True, capture_output=True,
        text=True).stdout
    require("There are no relocations" in relocations,
            "bootshim ELF still contains relocations")
    undefined = subprocess.run(
        ["llvm-nm", "-u", str(elf)], check=True, capture_output=True,
        text=True).stdout.strip()
    require(not undefined, f"bootshim ELF has undefined symbols: {undefined}")

    require(len(capsule) >= 64, "capsule is truncated")
    fields = struct.unpack_from("<8sIIQQQQQQ", capsule)
    magic, version, header_size, total_size, generation, payload_offset, \
        payload_size, payload_receipt, flags = fields
    require(magic == b"DUCHLKR1" and version == 1 and header_size == 64,
            "capsule identity is invalid")
    require(total_size == len(capsule) and payload_offset == 64 and
            payload_size == len(payload) and
            capsule[payload_offset:] == payload,
            "capsule does not contain the exact payload")
    require(generation != 0 and flags == 1 and
            payload_receipt == receipt(payload),
            "capsule generation, flags or receipt is invalid")

    payload_facts = parse_payload(payload)

    require(len(fdt) >= 40 and fdt[:4] == bytes.fromhex("d00dfeed"),
            "captured FDT header is invalid")
    fdt_size = struct.unpack_from(">I", fdt, 4)[0]
    require(40 <= fdt_size <= len(fdt), "captured FDT size is invalid")
    image_range = (IMAGE_LOAD, len(image))
    fdt_range = (FDT_LOAD, max(fdt_size, FDT_RESERVE))
    staging_range = (STAGING_BASE, len(payload))
    xnu_range = (XNU_BASE, XNU_SIZE)
    ranges = {
        "fdt": fdt_range,
        "image": image_range,
        "staging": staging_range,
        "xnu": xnu_range,
    }
    names = list(ranges)
    for index, first_name in enumerate(names):
        first = ranges[first_name]
        for second_name in names[index + 1:]:
            second = ranges[second_name]
            require(not overlap(first[0], first[1], second[0], second[1]),
                    f"{first_name} overlaps {second_name}")
    qemu_end = QEMU_RAM_BASE + QEMU_RAM_SIZE
    for name, (start, size) in ranges.items():
        require(QEMU_RAM_BASE <= start and start + size <= qemu_end,
                f"{name} lies outside QEMU's 8 GiB RAM")
    require(len(payload) <= STAGING_CAPACITY,
            "payload exceeds the QEMU-only staging capacity")
    guard_tool = Path(__file__).resolve().parents[2] / \
        "tools" / "duchamp-loader-guard.py"
    require(guard_tool.is_file(), f"missing loader guard: {guard_tool}")
    guard_run = subprocess.run(
        [sys.executable, str(guard_tool), "--fdt", str(args.fdt.resolve()),
         "--payload", str(args.payload.resolve()), "--occupied",
         f"{IMAGE_LOAD:#x}:{len(image):#x}", "--occupied",
         f"{STAGING_BASE:#x}:{len(payload):#x}"],
        capture_output=True, text=True)
    require(guard_run.returncode == 0,
            "loader guard rejected the full layout: " +
            (guard_run.stderr.strip() or guard_run.stdout.strip()))
    guard_result = json.loads(guard_run.stdout)
    require(guard_result.get("decision") == "plan-valid-no-copy-performed" and
            guard_result.get("phone_accessed") is False and
            guard_result.get("copy_performed") is False and
            guard_result.get("jump_performed") is False,
            "loader guard did not return the expected no-copy decision")
    result = {
        "result": "PASS",
        "mode": "qemu-only",
        "elf": str(elf),
        "image_sha256": sha256(image),
        "image_size": len(image),
        "image_load": IMAGE_LOAD,
        "capsule_sha256": sha256(capsule),
        "capsule_offset": capsule_offset,
        "capsule_size": len(capsule),
        "generation": generation,
        "payload_sha256": sha256(payload),
        "payload_size": len(payload),
        "payload_segments": payload_facts["segment_count"],
        "payload_entry": payload_facts["entry"],
        "payload_boot_args": payload_facts["boot_args"],
        "loader_guard": guard_result,
        "payload_receipt": f"0x{payload_receipt:016x}",
        "fdt_sha256": sha256(fdt),
        "fdt_size": fdt_size,
        "staging_base": STAGING_BASE,
        "xnu_base": XNU_BASE,
        "xnu_size": XNU_SIZE,
        "report_pa": (IMAGE_LOAD +
                      symbols["duchamp_lk_ram_boot_report"] - head),
        "relocations": 0,
        "undefined_symbols": 0,
    }
    if args.boot_image:
        result["boot_wrapper"] = verify_boot_wrapper(
            args.boot_image.resolve(), args.stock_boot.resolve(), image)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n")
    print("lk-ram-layout: PASS "
          f"image={len(image)} capsule_offset={capsule_offset:#x} "
          f"payload={len(payload)} generation={generation:#x} "
          f"report_pa={result['report_pa']:#x}")
    if args.boot_image:
        wrapper = result["boot_wrapper"]
        print("lk-ram-boot-wrapper: PASS "
              f"size={wrapper['size']} kernel={wrapper['kernel_size']} "
              f"format={wrapper['kernel_format']} "
              "avb_payload_hash=expected-mismatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
