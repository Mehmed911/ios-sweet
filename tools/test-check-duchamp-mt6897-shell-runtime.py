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

    def test_runtime_contract_probes_are_read_only_and_bounded(self):
        self.assertEqual(
            MODULE.PROBES["ufs_dma_mask_bits"],
            (
                "exec-out",
                "cat",
                "/sys/devices/platform/soc/112b0000.ufshci/dma_mask_bits",
            ),
        )
        self.assertEqual(MODULE.parse_dma_mask_bits("64"), 64)
        with self.assertRaisesRegex(ValueError, "outside 1..64"):
            MODULE.parse_dma_mask_bits("0")
        with self.assertRaisesRegex(ValueError, "outside 1..64"):
            MODULE.parse_dma_mask_bits("65")
        self.assertEqual(
            MODULE.parse_bounded_nonnegative_integer("8", "nr_hw_queues"), 8
        )
        with self.assertRaisesRegex(ValueError, "outside"):
            MODULE.parse_bounded_nonnegative_integer("-1", "nr_hw_queues")

    def test_recursive_inventory_does_not_infer_hidden_contracts(self):
        inventory = MODULE.parse_ufs_interface_inventory(
            "-r--r--r-- 1 root root 4096 capabilities\n"
            "-r--r--r-- 1 root root 4096 nr_hw_queues\n"
        )
        self.assertEqual(inventory["hccap_candidate_entries"], [])
        self.assertEqual(inventory["dma_mask_candidate_entries"], [])
        inventory = MODULE.parse_ufs_interface_inventory(
            "-r--r--r-- 1 root root 4096 hccap\n"
            "-r--r--r-- 1 root root 4096 dma_mask_bits\n"
        )
        self.assertEqual(inventory["hccap_candidate_entries"], ["hccap"])
        self.assertEqual(inventory["dma_mask_candidate_entries"], ["dma_mask_bits"])

    def test_bounded_proc_debug_exposes_hccap_but_not_dma_mask(self):
        parsed = MODULE.parse_ufs_proc_debug(
            "Host capabilities=0x55c7051f, hba-caps=0x1c5, mtk-caps:0x6c0\n"
            "ver. host=0x400, dev=0x400\n"
            "MCQ sup./en.: 1/1, nr_hw_queues=8\n"
            "nutrs=64, dev_info.bqueuedepth=64\n"
        )
        self.assertEqual(parsed["effective_host_capabilities"], "0x55c7051f")
        self.assertTrue(parsed["supports_64_bit_addressing"])
        self.assertTrue(parsed["mcq_supported"])
        self.assertTrue(parsed["mcq_enabled"])
        self.assertEqual(parsed["nr_hw_queues"], 8)
        self.assertIsNone(parsed["effective_dma_mask_bits"])

        with self.assertRaisesRegex(ValueError, "MCQ support conflicts"):
            MODULE.parse_ufs_proc_debug(
                "Host capabilities=0x15c7051f, hba-caps=0x1c5, mtk-caps:0x6c0\n"
                "ver. host=0x400, dev=0x400\n"
                "MCQ sup./en.: 1/1, nr_hw_queues=8\n"
                "nutrs=64, dev_info.bqueuedepth=64\n"
            )

    def test_swiotlb_policy_is_parsed_without_inferring_pool_state(self):
        self.assertEqual(
            MODULE.kernel_cmdline_value(
                "root=/dev/ram swiotlb=noforce disable_dma32=on", "swiotlb"
            ),
            "noforce",
        )
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            MODULE.kernel_cmdline_value("root=/dev/ram", "swiotlb")

    def test_cmdline_probe_preserves_unknown_and_permission_denied(self):
        self.assertEqual(
            MODULE.kernel_cmdline_observation(
                completed([], b"root=/dev/ram swiotlb=noforce\n")
            ),
            {"status": "specified", "value": "noforce"},
        )
        self.assertEqual(
            MODULE.kernel_cmdline_observation(completed([], b"root=/dev/ram\n")),
            {"status": "not-specified", "value": None},
        )
        self.assertEqual(
            MODULE.kernel_cmdline_observation(
                completed([], b"cat: /proc/cmdline: Permission denied\n")
            ),
            {"status": "permission-denied", "value": None},
        )
        with self.assertRaisesRegex(ValueError, "unambiguous"):
            MODULE.kernel_cmdline_observation(
                completed([], b"swiotlb=noforce swiotlb=force\n")
            )

    def test_bounded_atf_identity_is_parsed_without_effect_claims(self):
        text = """\
NOTICE: BL31: lts-v2.8.6(release):2fbca47
NOTICE: BL31: Built : 07:19:18, Dec 18 2024
NOTICE: Software version: common_2.6.1(6897-1.2)
NOTICE: Build time: Jun 8 2022(Jul 25 20:00:00 UTC 2023)
"""
        self.assertEqual(
            MODULE.parse_atf_identity(text),
            {
                "status": "observed",
                "release": "lts-v2.8.6(release):2fbca47",
                "built": "07:19:18, Dec 18 2024",
                "software_version": "common_2.6.1(6897-1.2)",
                "software_build_time": "Jun 8 2022(Jul 25 20:00:00 UTC 2023)",
            },
        )
        self.assertEqual(
            MODULE.parse_atf_identity("")["status"],
            "not-found-in-bounded-capture",
        )
        with self.assertRaisesRegex(ValueError, "partial BL31 identity"):
            MODULE.parse_atf_identity("NOTICE: BL31: Built : today\n")

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

    def test_root_read_only_command_gate_is_exact(self):
        seen = []

        def runner(argv, **_kwargs):
            seen.append(argv)
            return completed(argv, b"uid=0(root) gid=0(root)\n")

        allowed = MODULE.ROOT_PROBES["identity"]
        process = MODULE.adb_root_read("adb", "serial", allowed, runner)
        self.assertIn(b"uid=0", process.stdout)
        self.assertEqual(seen[0][3:], list(allowed))
        for command in (
            ("exec-out", "su", "-c", "dd if=/dev/block/x"),
            ("exec-out", "su", "-c", "cat /dev/block/x"),
            ("exec-out", "su", "-c", "echo 1 > /sys/example"),
        ):
            with self.assertRaisesRegex(ValueError, "non-allowlisted"):
                MODULE.adb_root_read("adb", "serial", command, runner)

        commands = "\n".join(command[-1] for command in MODULE.ROOT_PROBES.values())
        for token in (">", "dd ", "/dev/block", "mount ", "setprop "):
            self.assertNotIn(token, commands)
        self.assertIn("timeout 2 head -c 262144", commands)
        self.assertIn("timeout 2 head -n 20 /proc/ufs_debug", commands)
        self.assertIn("timeout 3 ls -laR", commands)
        self.assertIn("timeout 3 dmesg", commands)

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
