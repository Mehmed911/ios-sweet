#!/usr/bin/env python3
"""Verify the isolated Duchamp runtime PC/x0 capture image offline."""

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import struct
import subprocess


SCRIPT_DIR = Path(__file__).resolve().parent
LAYOUT_SCRIPT = SCRIPT_DIR / "verify-duchamp-phone-layout.py"
LAYOUT_SPEC = importlib.util.spec_from_file_location(
    "duchamp_phone_layout_contract", LAYOUT_SCRIPT)
LAYOUT = importlib.util.module_from_spec(LAYOUT_SPEC)
LAYOUT_SPEC.loader.exec_module(LAYOUT)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


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


def signed(value, bits):
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def adr_target(instruction, pc, register):
    require(instruction & 0x9F00001F == 0x10000000 | register,
            f"capture sequence lacks adr x{register}")
    immediate = ((((instruction >> 5) & 0x7FFFF) << 2) |
                 ((instruction >> 29) & 3))
    return pc + signed(immediate, 21)


def call_target(instruction, pc):
    require(instruction & 0xFC000000 == 0x94000000,
            "capture sequence does not call its isolated main")
    return pc + (signed(instruction & 0x3FFFFFF, 26) << 2)


def verify_capture_store(image, symbols):
    head = symbols["_head"]
    capture = symbols["duchamp_phone_capture_store_entry_pc"]
    runtime_head = symbols["duchamp_bootshim_runtime_head"]
    main = symbols["duchamp_bootshim_main"]

    def word(address):
        offset = address - head
        require(0 <= offset <= len(image) - 4,
                "capture instruction lies outside Image")
        return struct.unpack_from("<I", image, offset)[0]

    require(adr_target(word(capture), capture, 1) == head,
            "runtime PC capture does not resolve to _head")
    require(adr_target(word(capture + 4), capture + 4, 2) == runtime_head,
            "runtime PC capture does not resolve to its RAM record")
    require(word(capture + 8) == 0xF9000041,
            "runtime PC capture lacks str x1, [x2]")
    require(call_target(word(capture + 12), capture + 12) == main,
            "capture sequence does not immediately enter isolated main")


def inspect_arm64_image(image):
    require(len(image) >= 64 and image[56:60] == b"ARM\x64",
            "phone-capture Image lacks an ARM64 header")
    text_offset, image_bytes, flags = struct.unpack_from("<QQQ", image, 8)
    require(text_offset == 0,
            "phone-capture Image is not position-independent at offset zero")
    require(image_bytes == len(image),
            "phone-capture Image header size differs from the file")
    require(flags == 0xA,
            "phone-capture Image flags are not little-endian/4-KiB")
    return {
        "bytes": len(image),
        "sha256": sha256(image),
        "text_offset": text_offset,
        "header_image_bytes": image_bytes,
        "flags": flags,
    }


def inspect_build(elf, image, ufs_handoff_probe=False):
    image_report = inspect_arm64_image(image)
    symbols = read_symbols(elf)
    required = (
        "_head", "_start", "duchamp_phone_capture_store_entry_pc",
        "duchamp_bootshim_runtime_head", "duchamp_bootshim_entry_state",
        "duchamp_bootshim_phone_capture_record", "duchamp_phone_capture_run",
        "duchamp_bootshim_main", "halt", "_end",
    )
    missing = [name for name in required if name not in symbols]
    require(not missing, f"phone-capture ELF is missing symbols: {missing}")
    require(symbols["_head"] == 0,
            "phone-capture ELF must remain position-independent at link base 0")
    require(symbols["_end"] - symbols["_head"] == len(image),
            "phone-capture ELF head/end differ from Image bytes")
    require(symbols["_start"] < symbols["duchamp_phone_capture_store_entry_pc"] <
            symbols["duchamp_bootshim_main"] < symbols["_end"],
            "phone-capture symbols are out of order")
    verify_capture_store(image, symbols)
    probe_symbol = "duchamp_bootshim_ufs_handoff_record"
    require((probe_symbol in symbols) == ufs_handoff_probe,
            "UFS handoff probe selection differs from the linked image")
    if ufs_handoff_probe:
        instructions = subprocess.check_output(
            ["llvm-objdump", "-d", str(elf)], text=True)
        require(not re.search(r"\b(?:smc|hvc)\s+#", instructions),
                "UFS handoff probe contains a secure-monitor or hypervisor call")

    forbidden = (
        "duchamp_phone_layout_guard", "duchamp_phone_layout_stop",
        "duchamp_enter_xnu", "duchamp_lk_ram_boot_run",
        "duchamp_embedded_payload_start", "duchamp_loader_materialize",
        "duchamp_handoff_ready_check", "duchamp_bootshim_xnu_return",
        "stop_watchdog", "fdt_header_valid", "draw_diagnostic",
    )
    present = [name for name in forbidden if name in symbols]
    require(not present,
            f"phone-capture ELF contains forbidden capability: {present}")
    capsule_start = symbols.get("duchamp_lk_ram_capsule_start")
    capsule_end = symbols.get("duchamp_lk_ram_capsule_end")
    require(capsule_start is not None and capsule_start == capsule_end,
            "phone-capture ELF contains a non-empty LK RAM capsule")

    relocations = subprocess.run(
        ["llvm-readelf", "-r", str(elf)], check=True,
        capture_output=True, text=True).stdout
    require("There are no relocations" in relocations,
            "phone-capture ELF still contains relocations")
    undefined = subprocess.run(
        ["llvm-nm", "-u", str(elf)], check=True,
        capture_output=True, text=True).stdout.strip()
    require(not undefined,
            "phone-capture ELF contains undefined symbols: " + undefined)
    return {
        "build_valid": True,
        "elf": str(elf.resolve()),
        "image": image_report,
        "static_head": symbols["_head"],
        "end": symbols["_end"],
        "capture_store": symbols["duchamp_phone_capture_store_entry_pc"],
        "runtime_head_record": symbols["duchamp_bootshim_runtime_head"],
        "capture_record": symbols["duchamp_bootshim_phone_capture_record"],
        "relocations": 0,
        "undefined_symbols": 0,
        "payload_transport_or_jump_linked": False,
        "fdt_dereference_linked": ufs_handoff_probe,
        "watchdog_access_linked": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--elf", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--ufs-handoff-probe", action="store_true")
    arguments = parser.parse_args()
    if (arguments.elf is None) != (arguments.image is None):
        parser.error("--elf and --image must be supplied together")
    if arguments.ufs_handoff_probe and arguments.elf is None:
        parser.error("--ufs-handoff-probe requires --elf and --image")
    if arguments.json_out and arguments.json_out.exists():
        parser.error("preserve existing output")
    try:
        contract = json.loads(arguments.contract.resolve().read_text(
            encoding="utf-8"))
        result = {
            "result": "PASS",
            "mode": ("ufs-handoff-receiver-offline-verification"
                     if arguments.ufs_handoff_probe else
                     "runtime-pc-x0-capture-offline-verification"),
            "contract": LAYOUT.validate_contract(contract),
            "build": None,
            "safety": {
                "position_independent": True,
                "ram_record_only": True,
                "framebuffer_write_linked": True,
                "fdt_dereference_linked": arguments.ufs_handoff_probe,
                "watchdog_access_linked": False,
                "storage_access_linked": False,
                "payload_transport_linked": False,
                "jump_to_xnu_linked": False,
                "phone_access_during_verification": False,
                "partition_write": False,
                "flash": False,
                "phone_execution_authorized": False,
            },
        }
        if arguments.elf:
            result["build"] = inspect_build(
                arguments.elf.resolve(), arguments.image.resolve().read_bytes(),
                arguments.ufs_handoff_probe)
        if arguments.json_out:
            arguments.json_out.parent.mkdir(parents=True, exist_ok=True)
            with arguments.json_out.open("x", encoding="utf-8") as output:
                output.write(json.dumps(result, indent=2) + "\n")
    except (OSError, ValueError, json.JSONDecodeError,
            subprocess.SubprocessError) as error:
        parser.exit(1, "phone-capture verification failed: " +
                    str(error) + "\n")
    if result["build"]:
        print("duchamp-phone-capture: PASS "
              f"link-base=0 bytes={result['build']['image']['bytes']} "
              f"payload=absent fdt-deref={'present' if arguments.ufs_handoff_probe else 'absent'} "
              "phone-run=not-authorized")
    else:
        print("duchamp-phone-capture-contract: PASS phone-run=not-authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
