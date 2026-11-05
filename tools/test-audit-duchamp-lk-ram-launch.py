#!/usr/bin/env python3
"""Unit tests for the offline Duchamp LK RAM-launch audit."""

import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools" / "audit-duchamp-lk-ram-launch.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_duchamp_lk_ram_launch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def encode_adrp(register, pc, target):
    delta = (target & ~0xFFF) - (pc & ~0xFFF)
    immediate = (delta >> 12) & ((1 << 21) - 1)
    return (0x90000000 | (immediate & 3) << 29 |
            (immediate >> 2) << 5 | register)


def encode_add_immediate(destination, source, immediate):
    return (0x91000000 | (immediate & 0xFFF) << 10 |
            source << 5 | destination)


def encode_bl(pc, target):
    return 0x94000000 | (((target - pc) >> 2) & 0x3FFFFFF)


class LkRamLaunchAuditTests(unittest.TestCase):
    def test_instruction_decoders_handle_forward_and_backward_values(self):
        pc = 0xFFFF000050700100
        target = 0xFFFF000050700300
        self.assertEqual(MODULE.decode_bl_target(encode_bl(pc, target), pc),
                         target)
        backward = pc - 0x80
        self.assertEqual(MODULE.decode_bl_target(encode_bl(pc, backward), pc),
                         backward)
        page_target = 0xFFFF000050712000
        register, decoded = MODULE.decode_adrp(
            encode_adrp(0, pc, page_target), pc)
        self.assertEqual((register, decoded), (0, page_target))

    def test_fixed_registration_recovery_resolves_x0_string(self):
        runtime_base = 0x100000
        register_va = runtime_base + 0x300
        raw = bytearray(0x400)
        command_offset = 0x220
        raw[command_offset:command_offset + 10] = b"download:\0"
        call_offset = 0x4C
        struct.pack_into("<I", raw, 0x40,
                         encode_adrp(0, runtime_base + 0x40,
                                     runtime_base + command_offset))
        struct.pack_into("<I", raw, 0x44,
                         encode_add_immediate(0, 0, command_offset))
        struct.pack_into("<I", raw, call_offset,
                         encode_bl(runtime_base + call_offset, register_va))
        calls = MODULE.direct_registration_calls(
            bytes(raw), 0, len(raw), runtime_base, register_va)
        self.assertEqual(calls, [call_offset])
        records = MODULE.recover_fixed_commands(
            bytes(raw), calls, -1, 0, len(raw), runtime_base)
        self.assertEqual(records[0]["command"], "download:")
        self.assertEqual(records[0]["string_partition_offset"],
                         command_offset)

    def test_exact_boot_string_does_not_imply_registration(self):
        raw = b"prefix\0boot\0reboot\0suffix"
        self.assertEqual(MODULE.exact_c_string_offsets(
            raw, "boot", 0, len(raw)), [7])

    def test_dynamic_table_rejects_invalid_bounds(self):
        raw = bytearray(0x400)
        runtime_base = 0x100000
        start_slot = 0x100
        end_slot = 0x108
        table_start = 0x180
        table_end = table_start + MODULE.LK_DYNAMIC_ENTRY_BYTES
        command_offset = 0x220
        raw[command_offset:command_offset + 10] = b"oem test\0"
        struct.pack_into("<Q", raw, start_slot,
                         runtime_base + table_start)
        struct.pack_into("<Q", raw, end_slot, runtime_base + table_end)
        struct.pack_into("<IIQQ", raw, table_start, 1, 0,
                         runtime_base + command_offset,
                         runtime_base + 0x300)
        with mock.patch.object(
                MODULE, "LK_DYNAMIC_TABLE_START_SLOT_VA",
                runtime_base + start_slot), mock.patch.object(
                    MODULE, "LK_DYNAMIC_TABLE_END_SLOT_VA",
                    runtime_base + end_slot):
            result = MODULE.recover_dynamic_commands(
                bytes(raw), 0, len(raw), runtime_base)
            self.assertEqual(result["entry_count"], 1)
            self.assertEqual(result["commands"][0]["command"], "oem test")
            struct.pack_into("<Q", raw, end_slot,
                             runtime_base + table_start + 1)
            with self.assertRaisesRegex(ValueError, "invalid.*bounds"):
                MODULE.recover_dynamic_commands(
                    bytes(raw), 0, len(raw), runtime_base)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            output.write_text("keep", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(SCRIPT), "--lk", "missing",
                 "--output", str(output)],
                capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertIn("refusing to overwrite", process.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
