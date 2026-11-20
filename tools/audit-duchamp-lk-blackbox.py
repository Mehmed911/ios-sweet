#!/usr/bin/env python3
"""Audit the saved Duchamp LK Blackbox writer without executing firmware.

No device transport, storage extraction, historical-record decoder or hardware
authorization is implemented. All offsets are bound to the pinned local image.
"""
import argparse
import hashlib
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM


LK_SHA256 = "f85373d3b4cdf3c959e38bbbfe198a2857e03a5266c6f2a40c319549a5ba957a"
BIAS = 0xffff000050700000 - 0x200
CHECKS = {
    0x51a58: "add x0, x0, #0xd66",
    0x51a6c: "mov w3, #0x400",
    0x51a70: "bl #0xffff000050765558",
    0x51b08: "ldp w6, w7, [x19, #0x10]",
    0x51bc8: "mov x2, x21",
    0x51bd0: "bl #0xffff000050765558",
    0x51c8c: "mov w8, #0x800000",
    0x51ce8: "ldr w3, [x8, #0x10]",
    0x51cfc: "ldp w11, w22, [x9, #0x14]",
    0x51d08: "cmp w11, #5",
    0x51d0c: "add w10, w10, #1",
    0x51d10: "csinc w24, w12, w11, eq",
    0x51d14: "str w10, [x8, #0x10]",
    0x51d18: "str w24, [x9, #0x14]",
    0x51d30: "sub w8, w24, #1",
    0x51d34: "madd w22, w8, w22, w23",
    0x51d4c: "bl #0xffff000050765558",
    0x51e94: "str w8, [x24, #0x14]",
    0x51f2c: "bl #0xffff0000507655c8",
    0x51f90: "bl #0xffff0000507655c8",
    0x51fec: "bl #0xffff0000507655c8",
    0x52050: "bl #0xffff000050751734",
    0x51990: "bl #0xffff0000507655c8",
    0x10050: "bl #0xffff000050751824",
    0x65780: "ldr x4, [x0, #0x70]",
    0x657f0: "ldr x4, [x0, #0x80]",
    0x9248: "bl #0xffff000050713fac",
    0x9250: "bl #0xffff000050713fb8",
}


def audit(raw):
    if hashlib.sha256(raw).hexdigest() != LK_SHA256:
        raise ValueError("LK differs from the reviewed Duchamp artifact")
    if raw[0xbef66:0xbef66 + 9] != b"blackbox\0":
        raise ValueError("Blackbox label mismatch")
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    rows = []
    for offset, expected in CHECKS.items():
        insn = next(md.disasm(raw[offset:offset + 4], offset + BIAS), None)
        actual = (insn.mnemonic + " " + insn.op_str) if insn else "invalid"
        if actual != expected:
            raise ValueError(f"file+{offset:#x}: {actual} != {expected}")
        rows.append({"file_offset": hex(offset), "instruction": actual})
    return {
        "scope": "static instruction audit of saved firmware; no firmware execution",
        "lk_sha256": LK_SHA256, "instruction_assertions": rows,
        "source_confirmed": {
            "storage_label": "blackbox",
            "writer_file_offset": "0x51a24",
            "caller_before_secure_handoff": "0x10050",
            "ring_cursor_values_after_write": [1, 2, 3, 4, 5],
            "cursor_wrap_comparison": 5,
            "printed_dump_count_is_cursor_not_capacity": True,
            "printed_generation_is_before_increment": True,
            "generation_field_bits": 32,
            "metadata_writes_precede_pl_lk_bytes": True,
            "retention_is_conditional_on_successful_storage_writes": True,
        },
        "unverified": ["historical Slot B record still retained", "complete storage writes",
                       "supported historical export in running Android", "record authentication",
                       "Slot B image identity and XNU entry", "final ownership and DMA isolation"],
        "historical_record_recovered": False, "physical_access_authorized": False,
        "phone_operations": [],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lk", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    report = audit(args.lk.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS {len(CHECKS)}/{len(CHECKS)} pinned instruction checks; no device access")


if __name__ == "__main__":
    main()
