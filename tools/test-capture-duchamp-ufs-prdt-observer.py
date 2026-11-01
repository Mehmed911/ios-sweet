#!/usr/bin/env python3
"""Tests for the fail-closed Duchamp PRDT live-observation runner."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools/capture-duchamp-ufs-prdt-observer.py"
SPEC = importlib.util.spec_from_file_location("capture_prdt", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def observation(**changes):
    values = {
        "observation_version": 2,
        "root_read_only": 1,
        "coherent_snapshot": 1,
        "runtime_direct_dma_contract": 1,
        "hook_calls": 0,
        "target_calls": 0,
        "rejected_calls": 0,
        "commands": 0,
        "segments": 0,
        "read_commands": 0,
        "write_commands": 0,
        "bidirectional_commands": 0,
        "unknown_direction_commands": 0,
        "hook_error_calls": 0,
        "zero_length_segments": 0,
        "dma_end_overflows": 0,
        "translated_phys_invalid": 0,
        "original_phys_end_overflows": 0,
        "prdt_address_mismatches": 0,
        "prdt_length_mismatches": 0,
        "swiotlb_segments": 0,
        "dma_to_phys_matches": 0,
        "dma_to_phys_mismatches": 0,
        "above_4g_segments": 0,
        "outside_bus_limit_segments": 0,
        "runtime_contract_changes": 0,
        "min_dma_address": 0,
        "max_dma_end": 0,
        "min_translated_phys": 0,
        "max_translated_phys_end": 0,
        "min_original_phys": 0,
        "max_original_phys_end": 0,
        "max_segment_length": 0,
        "runtime_bus_dma_limit": MODULE.EXPECTED_BUS_DMA_LIMIT,
        "observation_complete": 0,
        "all_prdt_entries_match": 0,
        "all_segments_within_bus_limit": 0,
        "all_dma_equals_original_without_swiotlb": 0,
    }
    values.update(changes)
    return values


def render(values):
    lines = []
    for key in sorted(values):
        value = values[key]
        if key in MODULE.HEX_FIELDS:
            value = f"0x{value:016x}"
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def completed(stdout=b"", stderr=b"", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class FakeTarget:
    def __init__(self, preexisting=False, unload_timeout=False):
        self.preexisting = preexisting
        self.unload_timeout = unload_timeout
        self.loaded = preexisting
        self.staged = False
        self.commands = []
        self.observation_reads = 0

    def command(self, *args, timeout=30):
        self.commands.append(("command",) + args)
        if args and args[0] == "push":
            self.staged = True
        return completed()

    def shell(self, *args, timeout=30):
        self.commands.append(("shell",) + args)
        values = {
            ("getprop", "ro.product.device"): b"duchamp\n",
            ("getprop", "ro.boot.hardware"): b"mt6897\n",
            ("getprop", "sys.boot_completed"): b"1\n",
            ("uname", "-r"): (MODULE.EXPECTED_KERNEL + "\n").encode(),
            ("dumpsys", "battery"): b"level: 80\n",
        }
        if args in values:
            return completed(values[args])
        if args[:2] == ("toybox", "timeout"):
            return completed()
        raise AssertionError("unexpected fake shell command: " + repr(args))

    def root(self, command, timeout=30):
        self.commands.append(("root", command))
        if command == "id":
            return completed(b"uid=0(root) gid=0(root)\n")
        if command == "cat /proc/sys/kernel/modules_disabled":
            return completed(b"0\n")
        if command == "cat /proc/sys/kernel/random/boot_id":
            return completed(b"boot-id\n")
        if command == "cat /proc/sys/kernel/tainted":
            return completed(b"12805\n")
        if command == "dmesg":
            return completed(b"baseline one\nbaseline two\n")
        if command == (
            "cat /sys/module/ufs_mediatek_mod/notes/.note.gnu.build-id"
        ):
            return completed(MODULE.EXPECTED_UFS_BUILD_ID_NOTE)
        if command.startswith("grep -q '^ufs_mediatek_mod '"):
            return completed()
        if command.startswith("test ! -d " + MODULE.ORPHAN_TRACE_INSTANCE):
            return completed()
        if command == f"test ! -d /sys/module/{MODULE.MODULE_NAME}":
            return completed(returncode=int(self.loaded))
        if command == f"test -d /sys/module/{MODULE.MODULE_NAME}":
            return completed(returncode=int(not self.loaded))
        if command == f"test ! -e {MODULE.SYSFS_ATTRIBUTE}":
            return completed(returncode=int(self.loaded))
        if command == f"test -r {MODULE.SYSFS_ATTRIBUTE}":
            return completed(returncode=int(not self.loaded))
        if command == f"toybox stat -c %a {MODULE.SYSFS_ATTRIBUTE}":
            return completed(b"400\n")
        if command.startswith("test ! -e /data/local/tmp/"):
            return completed(returncode=int(self.staged))
        if command.startswith("test -e /data/local/tmp/"):
            return completed(returncode=int(not self.staged))
        if command.startswith("chmod 0400 /data/local/tmp/"):
            return completed()
        if command.startswith("toybox sha256sum /data/local/tmp/"):
            return completed(("a" * 64 + "  staged.ko\n").encode())
        if command.startswith("insmod /data/local/tmp/"):
            self.loaded = True
            return completed()
        if command == f"rmmod {MODULE.MODULE_NAME}":
            if self.unload_timeout:
                raise subprocess.TimeoutExpired(command, timeout)
            self.loaded = False
            return completed()
        if command.startswith("rm -f /data/local/tmp/"):
            self.staged = False
            return completed()
        if command == f"cat {MODULE.SYSFS_ATTRIBUTE}":
            self.observation_reads += 1
            if self.observation_reads == 1:
                return completed(render(observation()).encode())
            return completed(render(observation(
                hook_calls=2,
                target_calls=2,
                commands=2,
                segments=2,
                read_commands=2,
                dma_to_phys_matches=2,
                min_dma_address=0x1000,
                max_dma_end=0x2FFF,
                min_translated_phys=0x1000,
                max_translated_phys_end=0x2FFF,
                min_original_phys=0x1000,
                max_original_phys_end=0x2FFF,
                max_segment_length=0x1000,
                observation_complete=1,
                all_prdt_entries_match=1,
                all_segments_within_bus_limit=1,
                all_dma_equals_original_without_swiotlb=1,
            )).encode())
        raise AssertionError("unexpected fake root command: " + command)


def run_fake_main(fake_target, temporary):
    root = Path(temporary)
    for name in ("adb.exe", "observer.ko", "observer.c", "verification.json"):
        (root / name).write_bytes(b"x")
    output = root / "output"
    module_hash = "a" * 64
    argv = [
        "capture",
        "--adb", str(root / "adb.exe"),
        "--module", str(root / "observer.ko"),
        "--source", str(root / "observer.c"),
        "--verification", str(root / "verification.json"),
        "--output", str(output),
        "--approval-token", MODULE.approval_token(module_hash),
    ]
    verification = {"module": {"sha256": module_hash}}
    devices = completed(b"List of devices attached\nSERIAL\tdevice\n")
    with (
        mock.patch.object(sys, "argv", argv),
        mock.patch.object(MODULE, "validate_static_verification",
                          return_value=verification),
        mock.patch.object(MODULE, "run", return_value=devices),
        mock.patch.object(MODULE, "AdbTarget", return_value=fake_target),
        mock.patch("builtins.print"),
    ):
        result = MODULE.main()
    return result, json.loads((output / "result.json").read_text())


class CapturePrdtTests(unittest.TestCase):
    def test_valid_inverse_translation_observation_passes(self):
        before = MODULE.parse_observation(render(observation()))
        after = MODULE.parse_observation(render(observation(
            hook_calls=4,
            target_calls=4,
            commands=4,
            segments=8,
            read_commands=4,
            dma_to_phys_matches=8,
            above_4g_segments=3,
            min_dma_address=0x1000,
            max_dma_end=0x100001FFF,
            min_translated_phys=0x1000,
            max_translated_phys_end=0x100001FFF,
            min_original_phys=0x1000,
            max_original_phys_end=0x100001FFF,
            max_segment_length=0x1000,
            observation_complete=1,
            all_prdt_entries_match=1,
            all_segments_within_bus_limit=1,
            all_dma_equals_original_without_swiotlb=1,
        )))
        result = MODULE.evaluate_observations(before, after)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["route_classification"],
            "dma-to-phys-returns-original-no-swiotlb-under-pinned-contract",
        )
        self.assertTrue(
            result["inverse_dma_translation_returns_original_phys"]
        )
        self.assertFalse(
            result["raw_dma_address_equals_original_phys_proven"]
        )

    def test_swiotlb_route_is_reported_without_being_rejected(self):
        before = observation()
        after = observation(
            hook_calls=1,
            target_calls=1,
            commands=1,
            segments=2,
            read_commands=1,
            swiotlb_segments=2,
            dma_to_phys_mismatches=2,
            min_dma_address=0x2000,
            max_dma_end=0x3FFF,
            min_translated_phys=0x4000,
            max_translated_phys_end=0x5FFF,
            min_original_phys=0x8000,
            max_original_phys_end=0x9FFF,
            max_segment_length=0x1000,
            observation_complete=1,
            all_prdt_entries_match=1,
            all_segments_within_bus_limit=1,
        )
        result = MODULE.evaluate_observations(before, after)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["route_classification"],
            "swiotlb-buffer-observed-under-pinned-contract",
        )

    def test_mismatch_fails_closed(self):
        before = observation()
        after = observation(
            hook_calls=1,
            target_calls=1,
            commands=1,
            segments=1,
            read_commands=1,
            dma_to_phys_matches=1,
            prdt_address_mismatches=1,
            min_dma_address=0x1000,
            max_dma_end=0x1FFF,
            min_translated_phys=0x1000,
            max_translated_phys_end=0x1FFF,
            min_original_phys=0x1000,
            max_original_phys_end=0x1FFF,
            max_segment_length=0x1000,
            all_segments_within_bus_limit=1,
            all_dma_equals_original_without_swiotlb=1,
        )
        result = MODULE.evaluate_observations(before, after)
        self.assertFalse(result["passed"])
        self.assertTrue(any("prdt_address_mismatches" in item
                            for item in result["errors"]))

    def test_parser_rejects_unknown_and_duplicate_fields(self):
        text = render(observation())
        with self.assertRaisesRegex(ValueError, "unexpected"):
            MODULE.parse_observation(text + "\nfuture_field=1")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MODULE.parse_observation(text + "\nsegments=0")

    def test_static_receipt_is_bound_to_source_and_module_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            module = root / "duchamp_ufs_prdt_observer.ko"
            source = root / "duchamp_ufs_prdt_observer.c"
            receipt = root / "verification.json"
            module.write_bytes(b"module")
            source.write_bytes(b"source")
            receipt.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "did not pass"):
                MODULE.validate_static_verification(module, source, receipt)

    def test_kernel_log_overlap_identifies_only_new_lines(self):
        new, comparable = MODULE.appended_kernel_lines(
            "one\ntwo\nthree", "two\nthree\nfour"
        )
        self.assertTrue(comparable)
        self.assertEqual(new, ["four"])

    def test_preexisting_state_is_never_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = FakeTarget(preexisting=True)
            result, report = run_fake_main(target, temporary)
            self.assertEqual(result, 1)
            self.assertFalse(report["passed"])
            root_commands = [item[1] for item in target.commands
                             if item[0] == "root"]
            self.assertNotIn(f"rmmod {MODULE.MODULE_NAME}", root_commands)
            self.assertFalse(any(command.startswith("rm -f ")
                                 for command in root_commands))

    def test_cleanup_timeout_is_reported_and_does_not_skip_file_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = FakeTarget(unload_timeout=True)
            result, report = run_fake_main(target, temporary)
            self.assertEqual(result, 1)
            self.assertFalse(report["passed"])
            self.assertTrue(any("module unload" in item
                                for item in report["errors"]))
            self.assertFalse(target.staged)
            self.assertTrue((Path(temporary) / "output/result.json").is_file())

    def test_approval_token_is_bound_to_complete_module_hash(self):
        first = MODULE.approval_token("a" * 64)
        second = MODULE.approval_token("b" * 64)
        self.assertNotEqual(first, second)
        self.assertTrue(first.endswith("A" * 64))

    def test_kernel_log_read_failure_cannot_be_treated_as_empty_log(self):
        target = mock.Mock()
        target.root.return_value = completed(
            stderr=b"dmesg: permission denied\n", returncode=1
        )
        with self.assertRaisesRegex(RuntimeError, "kernel log failed"):
            MODULE.kernel_log_tail(target)

    def test_extended_kernel_fault_patterns_are_rejected(self):
        for line in (
            "WARNING: suspicious state",
            "SError Interrupt on CPU0",
            "rcu: RCU stall detected",
            "INFO: task dd blocked for more than 120 seconds (hung task)",
        ):
            self.assertRegex(line, MODULE.KERNEL_FAULT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
