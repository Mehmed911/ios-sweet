#!/usr/bin/env python3
"""Unit tests for the read-only Duchamp ADB runtime checker."""

import importlib.util
from pathlib import Path
import subprocess
import unittest


REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "tools/check-duchamp-mt6897-shell-runtime.py"
SPEC = importlib.util.spec_from_file_location("duchamp_shell_runtime", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
RUNTIME = MODULE.load_live_parser(REPO)


def completed(argv, stdout=b"", stderr=b"", returncode=0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def interrupts(timer, ufs):
    rows = ["           CPU0       CPU1"]
    rows.append(f" 20: {timer[0]:10d} {timer[1]:10d} GICv3  27 Level arch_timer")
    for offset, hwirq in enumerate((200, 209, 210, 211, 212, 213, 214, 215, 216)):
        counts = ufs[offset]
        rows.append(
            f" {500 + offset}: {counts[0]:10d} {counts[1]:10d} "
            f"GICv3 {hwirq} Level ufshcd"
        )
    return "\n".join(rows)


class ShellRuntimeTests(unittest.TestCase):
    def test_boot_device_must_name_the_saved_ufs_controller(self):
        self.assertEqual(
            MODULE.validate_boot_devices(
                "bootdevice,soc/112b0000.ufshci,112b0000.ufshci"
            ),
            ["bootdevice", "soc/112b0000.ufshci", "112b0000.ufshci"],
        )
        with self.assertRaisesRegex(ValueError, "does not identify"):
            MODULE.validate_boot_devices("bootdevice,soc/other")

    def test_probe_classifies_adb_exec_out_permission_text(self):
        denied = MODULE.probe_result(
            completed([], b"cat: /proc/iomem: Permission denied\n", returncode=0)
        )
        self.assertEqual(denied["status"], "permission-denied")
        self.assertFalse(denied["readable"])
        readable = MODULE.probe_result(completed([], b"arch_sys_counter\n"))
        self.assertEqual(readable["status"], "readable")
        self.assertTrue(readable["readable"])

    def test_read_only_command_gate(self):
        seen = []

        def runner(argv, **_kwargs):
            seen.append(argv)
            return completed(argv, b"duchamp\n")

        process = MODULE.adb_read(
            "adb", "serial", ("shell", "getprop", "ro.product.device"), runner
        )
        self.assertEqual(process.stdout, b"duchamp\n")
        self.assertEqual(seen[0][3:5], ["shell", "getprop"])
        for command in (
            ("shell", "su", "-c", "id"),
            ("exec-out", "dd", "if=/dev/block/x"),
            ("shell", "getprop", "push"),
        ):
            with self.assertRaisesRegex(ValueError, "refusing"):
                MODULE.adb_read("adb", "serial", command, runner)

    def test_exact_timer_and_all_nine_ufs_interrupts_advance(self):
        before_ufs = [(10 + index, 20 + index) for index in range(9)]
        after_ufs = [(11 + index, 22 + index) for index in range(9)]
        report = MODULE.verify_interrupt_progress(
            interrupts((100, 200), before_ufs),
            interrupts((105, 207), after_ufs),
            [26, 27, 29, 30],
            [200, 209, 210, 211, 212, 213, 214, 215, 216],
            RUNTIME,
        )
        self.assertEqual(report["timer"]["gic_hwirq"], 27)
        self.assertEqual(report["timer"]["total_delta"], 12)
        self.assertEqual(report["ufs"]["total_delta"], 27)

    def test_missing_ufs_irq_is_rejected(self):
        values = [(10 + index, 20 + index) for index in range(9)]
        before = interrupts((100, 200), values)
        after = interrupts((105, 207), [(a + 1, b + 1) for a, b in values])
        after = "\n".join(line for line in after.splitlines() if "GICv3 216 " not in line)
        with self.assertRaisesRegex(ValueError, "differ from the saved DTB"):
            MODULE.verify_interrupt_progress(
                before,
                after,
                [26, 27, 29, 30],
                [200, 209, 210, 211, 212, 213, 214, 215, 216],
                RUNTIME,
            )

    def test_zero_ufs_progress_is_rejected(self):
        values = [(10 + index, 20 + index) for index in range(9)]
        with self.assertRaisesRegex(ValueError, "UFS IRQ counters did not advance"):
            MODULE.verify_interrupt_progress(
                interrupts((100, 200), values),
                interrupts((105, 207), values),
                [26, 27, 29, 30],
                [200, 209, 210, 211, 212, 213, 214, 215, 216],
                RUNTIME,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
