#!/usr/bin/env python3
"""Verify the fail-closed Duchamp phone-layout build without running it."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess


IMAGE_BASE = 0x40000000
FDT_ADDRESS = 0x47C80000
LK_PHYSICAL_BASE = 0x50700000
LK_SMC_FUNCTION_ID = 0xC2000115
EXPECTED_HASHES = {
    "lk": "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a",
    "boot": "1b972f4f1c98428f2fca1e7c1c8cf463e0122a70a290e482be3230c7838e3e12",
    "vendor_boot": "d1d1887eba4f7b4920fc4292de5cf4e9aa6e7ce474a6b45ffeb4141434743e49",
    "fdt": "9c49589f70044127be8941a9ea5537977f440ccd5ac15cfd24e120c8a1181d29",
    "iomem": "b6bf43ce2bcbe1d5d425b46977afe238653859f61403339b674a2c065054f833",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_contract(report):
    require(report.get("report_version") == 1 and
            report.get("result") == "PASS",
            "handoff contract did not pass")
    require(report.get("decision") ==
            "offline-layout-documented-phone-execution-blocked",
            "handoff contract decision differs")
    inputs = report.get("inputs", {})
    for name, digest in EXPECTED_HASHES.items():
        require(inputs.get(name, {}).get("sha256") == digest,
                f"handoff contract {name} receipt differs")
    mapping = report.get("lk", {}).get("self_bootstrap_mapping", {})
    handoff = report.get("lk", {}).get("linux_handoff", {})
    image = report.get("android_image_contract", {})
    fdt = report.get("fdt_handoff", {})
    claims = report.get("claims", {})
    layout = report.get("phone_layout", {})
    safety = report.get("safety", {})
    require(mapping.get("physical_base") == LK_PHYSICAL_BASE,
            "LK physical base differs")
    require(mapping.get("runtime_pc_register_captured") is False,
            "contract improperly claims a runtime LK PC capture")
    require(handoff.get("smc_function_id") == LK_SMC_FUNCTION_ID and
            handoff.get("kernel_target_is_fixed_in_lk_binary") is False and
            handoff.get("fdt_target_is_fixed_in_lk_binary") is False,
            "LK dynamic SMC handoff contract differs")
    require(image.get("load_address") == IMAGE_BASE and
            image.get("runtime_entry_pc_captured") is False,
            "Android Image static contract differs")
    require(fdt.get("address") == FDT_ADDRESS and
            fdt.get("incoming_x0_value_captured") is False and
            fdt.get("dtb_self_describes_physical_address") is False,
            "FDT corroboration boundary differs")
    require(layout.get("image_base") == IMAGE_BASE and
            layout.get("image_ceiling_exclusive") == FDT_ADDRESS and
            layout.get("expected_entry_x0") == FDT_ADDRESS and
            layout.get("execution_authorized") is False,
            "phone-layout boundary differs")
    require(claims.get("phone_layout_preflight_permitted") is True and
            claims.get("phone_execution_ready") is False and
            claims.get("android_image_runtime_entry_pc_captured") is False and
            claims.get("fdt_incoming_x0_captured") is False,
            "contract crosses the static/runtime evidence boundary")
    for key in ("phone_access", "adb_access", "fastboot_access",
                "partition_write", "flash", "mmio_access",
                "firmware_execution", "jump_to_xnu"):
        require(safety.get(key) is False,
                f"unsafe handoff-contract flag: {key}")
    return {
        "contract_valid": True,
        "lk_physical_base": LK_PHYSICAL_BASE,
        "image_base": IMAGE_BASE,
        "fdt_address": FDT_ADDRESS,
        "execution_authorized": False,
    }


def read_symbols(elf):
    process = subprocess.run(
        ["llvm-nm", "-n", str(elf)], check=True, capture_output=True,
        text=True)
    symbols = {}
    for line in process.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3:
            try:
                symbols[fields[2]] = int(fields[0], 16)
            except ValueError:
                pass
    return symbols


def inspect_arm64_image(image):
    require(len(image) >= 64 and image[56:60] == b"ARM\x64",
            "phone-layout Image lacks an ARM64 header")
    text_offset, image_bytes, flags = struct.unpack_from("<QQQ", image, 8)
    require(text_offset == 0, "phone-layout Image text_offset is not zero")
    require(image_bytes == len(image),
            "phone-layout Image header size differs from the file")
    require(flags == 0xA,
            "phone-layout Image flags are not little-endian/4-KiB")
    return {
        "bytes": len(image),
        "sha256": sha256(image),
        "text_offset": text_offset,
        "header_image_bytes": image_bytes,
        "flags": flags,
    }


def signed(value, bits):
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def conditional_branch_target(instruction, pc):
    require(instruction & 0xFF000010 == 0x54000000 and
            instruction & 0xF == 1,
            "phone-layout guard lacks b.ne")
    return pc + (signed((instruction >> 5) & 0x7FFFF, 19) << 2)


def direct_branch_target(instruction, pc):
    require(instruction & 0x7C000000 == 0x14000000,
            "phone-layout stop lacks direct branch")
    return pc + (signed(instruction & 0x3FFFFFF, 26) << 2)


def verify_guard_code(image, symbols):
    head = symbols["_head"]
    start = symbols["_start"]
    guard = symbols["duchamp_phone_layout_guard"]
    stop = symbols["duchamp_phone_layout_stop"]
    halt = symbols["halt"]

    def word(address):
        offset = address - head
        require(0 <= offset <= len(image) - 4,
                "phone-layout guard instruction lies outside Image")
        return struct.unpack_from("<I", image, offset)[0]

    expected_prefix = (
        0xD5034FDF,  # msr daifset, #0xf
        0xAA0003F3,  # mov x19, x0
        0xAA0103F4,  # mov x20, x1
        0xAA0203F5,  # mov x21, x2
        0xAA0303F6,  # mov x22, x3
        0x910003F7,  # mov x23, sp
    )
    require(guard == start + len(expected_prefix) * 4,
            "phone-layout guard is not the first operation after entry capture")
    require(tuple(word(start + index * 4)
                  for index in range(len(expected_prefix))) == expected_prefix,
            "phone-layout entry prefix differs")

    adr = word(guard)
    require(adr & 0x9F00001F == 0x1000000B,
            "phone-layout guard lacks adr x11")
    adr_immediate = (((adr >> 5) & 0x7FFFF) << 2) | ((adr >> 29) & 3)
    require(guard + signed(adr_immediate, 21) == head,
            "phone-layout adr does not resolve to _head")
    require(word(guard + 4) == 0xD2A80009 and
            word(guard + 8) == 0xEB09017F,
            "phone-layout image-base comparison differs")
    require(conditional_branch_target(word(guard + 12), guard + 12) == halt,
            "phone-layout image-base failure does not stop")
    require(word(guard + 16) == 0xD2A8F90A and
            word(guard + 20) == 0xEB0A027F,
            "phone-layout FDT comparison differs")
    require(conditional_branch_target(word(guard + 24), guard + 24) == halt,
            "phone-layout FDT failure does not stop")
    require(stop == guard + 28 and
            direct_branch_target(word(stop), stop) == halt,
            "phone-layout success path does not stop")


def inspect_build(elf, image):
    image_report = inspect_arm64_image(image)
    symbols = read_symbols(elf)
    required = ("_head", "_start", "duchamp_phone_layout_guard",
                "duchamp_phone_layout_stop", "halt", "_end")
    missing = [name for name in required if name not in symbols]
    require(not missing, f"phone-layout ELF is missing symbols: {missing}")
    require(symbols["_head"] == IMAGE_BASE,
            "phone-layout ELF is not linked at the static Image contract")
    require(symbols["_end"] - symbols["_head"] == len(image),
            "phone-layout ELF head/end differ from Image bytes")
    require(symbols["_head"] <= symbols["_start"] <=
            symbols["duchamp_phone_layout_guard"] <
            symbols["duchamp_phone_layout_stop"] < symbols["_end"],
            "phone-layout guard symbols are out of order")
    require(symbols["_end"] <= FDT_ADDRESS,
            "phone-layout Image reaches the corroborated FDT address")
    verify_guard_code(image, symbols)
    forbidden = ("duchamp_enter_xnu", "duchamp_lk_ram_boot_run",
                 "duchamp_embedded_payload_start")
    present = [name for name in forbidden if name in symbols]
    require(not present,
            f"phone-layout ELF contains execution/transport symbols: {present}")
    capsule_start = symbols.get("duchamp_lk_ram_capsule_start")
    capsule_end = symbols.get("duchamp_lk_ram_capsule_end")
    require(capsule_start is not None and capsule_start == capsule_end,
            "phone-layout ELF contains a non-empty LK RAM capsule")
    relocations = subprocess.run(
        ["llvm-readelf", "-r", str(elf)], check=True,
        capture_output=True, text=True).stdout
    require("There are no relocations" in relocations,
            "phone-layout ELF still contains relocations")
    undefined = subprocess.run(
        ["llvm-nm", "-u", str(elf)], check=True,
        capture_output=True, text=True).stdout.strip()
    require(not undefined,
            "phone-layout ELF contains undefined symbols: " + undefined)
    return {
        "build_valid": True,
        "elf": str(elf.resolve()),
        "image": image_report,
        "head": symbols["_head"],
        "end": symbols["_end"],
        "fdt_ceiling": FDT_ADDRESS,
        "guard_symbol": symbols["duchamp_phone_layout_guard"],
        "stop_symbol": symbols["duchamp_phone_layout_stop"],
        "relocations": 0,
        "undefined_symbols": 0,
        "execution_capability_linked": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--elf", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--json-out", type=Path)
    arguments = parser.parse_args()
    if (arguments.elf is None) != (arguments.image is None):
        parser.error("--elf and --image must be supplied together")
    if arguments.json_out and arguments.json_out.exists():
        parser.error("preserve existing output")
    try:
        contract = json.loads(arguments.contract.resolve().read_text(
            encoding="utf-8"))
        result = {
            "result": "PASS",
            "mode": "phone-layout-preflight-only",
            "contract": validate_contract(contract),
            "build": None,
            "safety": {
                "local_files_only": True,
                "phone_access": False,
                "partition_write": False,
                "flash": False,
                "jump_to_xnu": False,
                "execution_authorized": False,
            },
        }
        if arguments.elf:
            result["build"] = inspect_build(
                arguments.elf.resolve(), arguments.image.resolve().read_bytes())
        if arguments.json_out:
            arguments.json_out.parent.mkdir(parents=True, exist_ok=True)
            with arguments.json_out.open("x", encoding="utf-8") as output:
                output.write(json.dumps(result, indent=2) + "\n")
    except (OSError, ValueError, json.JSONDecodeError,
            subprocess.SubprocessError) as error:
        parser.exit(1, "phone-layout verification failed: " +
                    str(error) + "\n")
    if result["build"]:
        print("duchamp-phone-layout: PASS "
              f"base={IMAGE_BASE:#x} bytes={result['build']['image']['bytes']} "
              f"fdt-ceiling={FDT_ADDRESS:#x} execution=blocked")
    else:
        print("duchamp-phone-contract: PASS execution=blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
