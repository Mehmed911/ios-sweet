#!/usr/bin/env python3
"""Audit the exact saved Duchamp LK for a documented RAM launch command.

This is a static, fail-closed audit.  It reads one pinned LK partition image,
decodes the AArch64 call sites that populate its Fastboot command registry,
and reports whether that registry contains a command that executes a payload
already downloaded to RAM.  It never contacts a phone, executes firmware,
performs MMIO, or changes a partition.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


LK_PARTITION_BYTES = 16 * 1024 * 1024
LK_SHA256 = "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a"
MTK_OUTER_MAGIC = 0x58881688
MTK_INNER_MAGIC = 0x58891689
LK_PAYLOAD_PARTITION_OFFSET = 0x200
LK_PAYLOAD_BYTES = 0xF1C70
LK_RUNTIME_BASE = 0xFFFF000050700000
LK_REGISTER_COMMAND_VA = 0xFFFF00005070705C
LK_DYNAMIC_TABLE_START_SLOT_VA = 0xFFFF0000507F1A58
LK_DYNAMIC_TABLE_END_SLOT_VA = 0xFFFF0000507F1A50
LK_DYNAMIC_ENTRY_BYTES = 0x18
LK_INTERNAL_HANDOFF_OFFSET = 0x10054
LK_INTERNAL_HANDOFF_SIGNATURE = bytes.fromhex(
    "a12280521f2003d5c06300100140b872"
    "e20313aae30316aae4031faa92250094"
)
LK_INTERNAL_SMC_ID = 0xC2000115
U64_MASK = (1 << 64) - 1

EXPECTED_DIRECT_CALL_OFFSETS = (
    0x7D9C, 0x7DB8, 0x7DD4, 0x7DF0, 0x7E0C, 0x7E28, 0x7E44,
    0x7E60, 0x7EFC, 0x9ED0, 0x9EEC, 0x9F08, 0x9F28, 0x9F44,
)
EXPECTED_CORE_COMMANDS = (
    "getvar:",
    "reboot",
    "reboot-bootloader",
    "reboot-fastboot",
    "reboot-recovery",
    "continue",
    "set_active:",
    "oem poweroff",
)
EXPECTED_TRANSFER_COMMANDS = (
    "download:",
    "flash:",
    "erase:",
    "oem ultraflash:",
    "oem ultraflash_en",
)
EXPECTED_DYNAMIC_COMMANDS = (
    "oem expdb",
    "oem lkmsg",
    "oem lpmsg",
    "oem uefilog",
    "oem fbreason",
    "oem unlock",
    "oem lock",
    "oem get_token",
    "oem lks",
    "oem chkmtklks",
    "oem setmtklks",
    "oem p2u",
    "oem dump_pllk_log",
    "oem printk-ratelimit",
    "oem usb2jtag",
    "oem off-mode-charge",
    "oem mrdump_out_set",
    "oem mrdump_fallocate",
    "oem mrdump_chkimg",
    "oem get_socid",
    "oem cdms",
    "oem allow-wipe-userdata",
)
RAM_EXECUTE_COMMANDS = frozenset({
    "boot", "boot:", "run", "run:", "execute", "execute:",
    "jump", "jump:", "go", "go:", "start", "start:",
    "chainload", "chainload:",
})


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def u32(raw, offset):
    require(0 <= offset <= len(raw) - 4, "truncated 32-bit value")
    return struct.unpack_from("<I", raw, offset)[0]


def u64(raw, offset):
    require(0 <= offset <= len(raw) - 8, "truncated 64-bit value")
    return struct.unpack_from("<Q", raw, offset)[0]


def sign_extend(value, bits):
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def partition_offset_to_va(offset, payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                           runtime_base=LK_RUNTIME_BASE):
    require(offset >= payload_offset, "offset precedes LK payload")
    return (runtime_base + offset - payload_offset) & U64_MASK


def va_to_partition_offset(address,
                           payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                           payload_bytes=LK_PAYLOAD_BYTES,
                           runtime_base=LK_RUNTIME_BASE):
    delta = (address - runtime_base) & U64_MASK
    require(delta < payload_bytes, "address is outside the LK payload map")
    return payload_offset + delta


def decode_bl_target(instruction, pc):
    if instruction & 0xFC000000 != 0x94000000:
        return None
    immediate = sign_extend(instruction & 0x03FFFFFF, 26) << 2
    return (pc + immediate) & U64_MASK


def decode_adr(instruction, pc):
    if instruction & 0x9F000000 != 0x10000000:
        return None
    immediate = ((instruction >> 5) & 0x7FFFF) << 2
    immediate |= (instruction >> 29) & 3
    immediate = sign_extend(immediate, 21)
    return instruction & 31, (pc + immediate) & U64_MASK


def decode_adrp(instruction, pc):
    if instruction & 0x9F000000 != 0x90000000:
        return None
    immediate = ((instruction >> 5) & 0x7FFFF) << 2
    immediate |= (instruction >> 29) & 3
    immediate = sign_extend(immediate, 21) << 12
    return instruction & 31, ((pc & ~0xFFF) + immediate) & U64_MASK


def decode_add_immediate(instruction):
    if instruction & 0xFF800000 != 0x91000000:
        return None
    shift = 12 if instruction & (1 << 22) else 0
    immediate = ((instruction >> 10) & 0xFFF) << shift
    return instruction & 31, (instruction >> 5) & 31, immediate


def read_c_string(raw, address, payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                  payload_bytes=LK_PAYLOAD_BYTES,
                  runtime_base=LK_RUNTIME_BASE, maximum=96):
    offset = va_to_partition_offset(
        address, payload_offset, payload_bytes, runtime_base)
    end_limit = min(payload_offset + payload_bytes, offset + maximum + 1)
    terminator = raw.find(b"\0", offset, end_limit)
    require(terminator >= 0, "unterminated LK command string")
    value = raw[offset:terminator]
    require(value and all(0x20 <= byte <= 0x7E for byte in value),
            "LK command is not printable ASCII")
    return value.decode("ascii"), offset


def resolve_x0_address(raw, call_offset, payload_offset,
                       payload_bytes, runtime_base, window=10):
    call_index = (call_offset - payload_offset) // 4
    first_index = max(0, call_index - window)
    add_index = None
    add_value = None
    for index in range(call_index - 1, first_index - 1, -1):
        offset = payload_offset + index * 4
        instruction = u32(raw, offset)
        decoded_adr = decode_adr(
            instruction,
            partition_offset_to_va(offset, payload_offset, runtime_base))
        if decoded_adr is not None and decoded_adr[0] == 0:
            return decoded_adr[1]
        decoded_add = decode_add_immediate(instruction)
        if (add_index is None and decoded_add is not None and
                decoded_add[0] == 0 and decoded_add[1] == 0):
            add_index = index
            add_value = decoded_add[2]
            continue
        if add_index is not None:
            decoded_adrp = decode_adrp(
                instruction,
                partition_offset_to_va(offset, payload_offset, runtime_base))
            if decoded_adrp is not None and decoded_adrp[0] == 0:
                return (decoded_adrp[1] + add_value) & U64_MASK
    return None


def direct_registration_calls(raw, payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                              payload_bytes=LK_PAYLOAD_BYTES,
                              runtime_base=LK_RUNTIME_BASE,
                              register_va=LK_REGISTER_COMMAND_VA):
    calls = []
    for offset in range(payload_offset, payload_offset + payload_bytes, 4):
        pc = partition_offset_to_va(offset, payload_offset, runtime_base)
        if decode_bl_target(u32(raw, offset), pc) == register_va:
            calls.append(offset)
    return calls


def recover_fixed_commands(raw, call_offsets, dynamic_call_offset,
                           payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                           payload_bytes=LK_PAYLOAD_BYTES,
                           runtime_base=LK_RUNTIME_BASE):
    records = []
    for call_offset in call_offsets:
        if call_offset == dynamic_call_offset:
            continue
        address = resolve_x0_address(
            raw, call_offset, payload_offset, payload_bytes, runtime_base)
        require(address is not None,
                f"cannot resolve x0 at registration call {call_offset:#x}")
        command, string_offset = read_c_string(
            raw, address, payload_offset, payload_bytes, runtime_base)
        records.append({
            "command": command,
            "call_partition_offset": call_offset,
            "call_partition_offset_hex": hex(call_offset),
            "call_va": partition_offset_to_va(
                call_offset, payload_offset, runtime_base),
            "call_va_hex": hex(partition_offset_to_va(
                call_offset, payload_offset, runtime_base)),
            "string_partition_offset": string_offset,
            "string_partition_offset_hex": hex(string_offset),
            "string_va": address,
            "string_va_hex": hex(address),
        })
    return records


def recover_dynamic_commands(raw,
                             payload_offset=LK_PAYLOAD_PARTITION_OFFSET,
                             payload_bytes=LK_PAYLOAD_BYTES,
                             runtime_base=LK_RUNTIME_BASE):
    start_slot = va_to_partition_offset(
        LK_DYNAMIC_TABLE_START_SLOT_VA, payload_offset, payload_bytes,
        runtime_base)
    end_slot = va_to_partition_offset(
        LK_DYNAMIC_TABLE_END_SLOT_VA, payload_offset, payload_bytes,
        runtime_base)
    table_start = u64(raw, start_slot)
    table_end = u64(raw, end_slot)
    require(table_start < table_end and
            (table_end - table_start) % LK_DYNAMIC_ENTRY_BYTES == 0,
            "invalid LK dynamic command table bounds")
    start_offset = va_to_partition_offset(
        table_start, payload_offset, payload_bytes, runtime_base)
    end_offset = va_to_partition_offset(
        table_end - 1, payload_offset, payload_bytes, runtime_base) + 1
    records = []
    for offset in range(start_offset, end_offset, LK_DYNAMIC_ENTRY_BYTES):
        policy0, policy1, command_va, handler_va = struct.unpack_from(
            "<IIQQ", raw, offset)
        require(handler_va != 0, "dynamic LK command has no handler")
        command, string_offset = read_c_string(
            raw, command_va, payload_offset, payload_bytes, runtime_base)
        records.append({
            "command": command,
            "entry_partition_offset": offset,
            "entry_partition_offset_hex": hex(offset),
            "entry_va": partition_offset_to_va(
                offset, payload_offset, runtime_base),
            "entry_va_hex": hex(partition_offset_to_va(
                offset, payload_offset, runtime_base)),
            "policy0": policy0,
            "policy1": policy1,
            "string_partition_offset": string_offset,
            "string_partition_offset_hex": hex(string_offset),
            "string_va": command_va,
            "string_va_hex": hex(command_va),
            "handler_va": handler_va,
            "handler_va_hex": hex(handler_va),
        })
    return {
        "start_va": table_start,
        "start_va_hex": hex(table_start),
        "end_va": table_end,
        "end_va_hex": hex(table_end),
        "entry_bytes": LK_DYNAMIC_ENTRY_BYTES,
        "entry_count": len(records),
        "commands": records,
    }


def exact_c_string_offsets(raw, value, payload_offset, payload_bytes):
    needle = value.encode("ascii") + b"\0"
    end = payload_offset + payload_bytes
    offsets = []
    cursor = payload_offset
    while True:
        cursor = raw.find(needle, cursor, end)
        if cursor < 0:
            return offsets
        if cursor == payload_offset or raw[cursor - 1] == 0:
            offsets.append(cursor)
        cursor += 1


def inspect_lk(raw):
    require(len(raw) == LK_PARTITION_BYTES, "lk_a size differs")
    require(sha256(raw) == LK_SHA256, "lk_a SHA-256 differs")
    require(u32(raw, 0) == MTK_OUTER_MAGIC,
            "LK outer package magic differs")
    require(u32(raw, 4) == LK_PAYLOAD_BYTES,
            "LK payload size differs")
    require(raw[8:40].split(b"\0", 1)[0] == b"lk",
            "first LK package entry is not lk")
    require(u32(raw, 0x30) == MTK_INNER_MAGIC and
            u32(raw, 0x34) == LK_PAYLOAD_PARTITION_OFFSET,
            "LK inner package header differs")
    require(raw[LK_INTERNAL_HANDOFF_OFFSET:
                LK_INTERNAL_HANDOFF_OFFSET +
                len(LK_INTERNAL_HANDOFF_SIGNATURE)] ==
            LK_INTERNAL_HANDOFF_SIGNATURE,
            "LK internal Linux handoff differs")

    calls = direct_registration_calls(raw)
    require(tuple(calls) == EXPECTED_DIRECT_CALL_OFFSETS,
            "LK Fastboot registration call sites differ")
    fixed = recover_fixed_commands(raw, calls, 0x7EFC)
    core = fixed[:len(EXPECTED_CORE_COMMANDS)]
    transfer = fixed[len(EXPECTED_CORE_COMMANDS):]
    require(tuple(item["command"] for item in core) ==
            EXPECTED_CORE_COMMANDS,
            "LK core Fastboot command set differs")
    require(tuple(item["command"] for item in transfer) ==
            EXPECTED_TRANSFER_COMMANDS,
            "LK transfer Fastboot command set differs")
    dynamic = recover_dynamic_commands(raw)
    require(tuple(item["command"] for item in dynamic["commands"]) ==
            EXPECTED_DYNAMIC_COMMANDS,
            "LK dynamic Fastboot command set differs")

    registered = [item["command"] for item in core]
    registered += [item["command"] for item in transfer]
    registered += [item["command"] for item in dynamic["commands"]]
    execution = [item for item in registered if item in RAM_EXECUTE_COMMANDS]
    boot_strings = exact_c_string_offsets(
        raw, "boot", LK_PAYLOAD_PARTITION_OFFSET, LK_PAYLOAD_BYTES)
    require(boot_strings, "LK payload no longer contains the boot string")
    require(not execution, "LK unexpectedly exposes a RAM execution command")

    return {
        "schema": "duchamp-mt6897-lk-ram-launch-audit-v1",
        "artifact": {
            "bytes": len(raw),
            "sha256": sha256(raw),
            "first_entry": "lk",
            "payload_partition_offset": LK_PAYLOAD_PARTITION_OFFSET,
            "payload_partition_offset_hex":
                hex(LK_PAYLOAD_PARTITION_OFFSET),
            "payload_bytes": LK_PAYLOAD_BYTES,
            "payload_bytes_hex": hex(LK_PAYLOAD_BYTES),
            "runtime_base": LK_RUNTIME_BASE,
            "runtime_base_hex": hex(LK_RUNTIME_BASE),
        },
        "fastboot_registry": {
            "registration_function_va": LK_REGISTER_COMMAND_VA,
            "registration_function_va_hex":
                hex(LK_REGISTER_COMMAND_VA),
            "direct_call_count": len(calls),
            "direct_call_partition_offsets": calls,
            "direct_call_partition_offsets_hex": [hex(item) for item in calls],
            "core_commands": core,
            "transfer_commands": transfer,
            "dynamic_table": dynamic,
            "registered_command_count": len(registered),
            "registered_commands": registered,
            "download_command_registered": "download:" in registered,
            "ram_execute_commands_registered": execution,
            "exact_boot_string_partition_offsets": boot_strings,
            "exact_boot_string_partition_offsets_hex":
                [hex(item) for item in boot_strings],
            "boot_string_is_registered_command": "boot" in registered,
            "interpretation": (
                "The exact LK contains a standalone 'boot' string and a "
                "Fastboot download command, but no recovered registry entry "
                "binds boot/run/execute/jump/go/start/chainload to a handler."
            ),
        },
        "internal_linux_handoff": {
            "status": "verified-in-exact-lk-binary",
            "partition_offset": LK_INTERNAL_HANDOFF_OFFSET,
            "partition_offset_hex": hex(LK_INTERNAL_HANDOFF_OFFSET),
            "mechanism": "internal-secure-monitor-call",
            "smc_function_id": LK_INTERNAL_SMC_ID,
            "smc_function_id_hex": hex(LK_INTERNAL_SMC_ID),
            "external_callback_abi_documented": False,
            "interpretation": (
                "The stock Linux handoff is an internal LK path.  Its SMC "
                "call site does not document a callable post-handoff LK or "
                "UEFI provider ABI."
            ),
        },
        "provider_decision": {
            "status": "unavailable-fail-closed",
            "ram_only_launch_provider_available": False,
            "phone_image_authorized": False,
            "reason_codes": [
                "fastboot-boot-not-registered",
                "no-registered-memory-execute-command",
                "internal-lk-handoff-is-not-an-external-provider-abi",
                "no-mt6897-uefi-provider-evidence-supplied-to-audit",
            ],
            "existing_lk_transport_role": (
                "consumer of an inherited immutable RAM capsule; it is not "
                "an entry mechanism"
            ),
            "required_to_open_gate": [
                "documented RAM-only caller that transfers control to the loader",
                "measured entry PC and x0/FDT contract for that caller",
                "documented EL, MMU, cache, memory ownership and lifetime contract",
                "repeatable no-partition-write recovery procedure",
            ],
        },
        "side_effects": {
            "phone_contacted": False,
            "firmware_executed": False,
            "mmio_performed": False,
            "partitions_modified": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lk", required=True,
                        help="exact saved Duchamp lk_a partition image")
    parser.add_argument("--output", help="new JSON report; never overwritten")
    parser.add_argument(
        "--require-provider", action="store_true",
        help="exit nonzero unless the audit proves a RAM launch provider")
    arguments = parser.parse_args()
    output = Path(arguments.output) if arguments.output else None
    if output is not None and output.exists():
        parser.error(f"refusing to overwrite existing output: {output}")
    try:
        path = Path(arguments.lk)
        raw = path.read_bytes()
        report = inspect_lk(raw)
        report["artifact"]["path"] = str(path.resolve())
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if output is not None:
            require(output.parent.is_dir(), "output directory does not exist")
            output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (OSError, ValueError) as error:
        print(f"audit-duchamp-lk-ram-launch: {error}", file=sys.stderr)
        return 2
    if (arguments.require_provider and not
            report["provider_decision"]["ram_only_launch_provider_available"]):
        print("audit-duchamp-lk-ram-launch: provider gate remains closed",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
