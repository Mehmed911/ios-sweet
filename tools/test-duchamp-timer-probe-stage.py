#!/usr/bin/env python3
"""Failure-atomicity and ordering tests for the pre-GIC timer probe."""

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("stage-duchamp-timer-probe.py")
SPEC = importlib.util.spec_from_file_location("timer_probe_stage", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


SOURCE = '''#include <arm/cpu_internal.h>
#if defined(DUCHAMP)
#include <arm/duchamp_timer_boot.h>
#endif
#if defined(DUCHAMP)
#include <arm/duchamp_counter_probe.h>
#endif
void arm_init(void)
{
\tcpu_machine_idle_init(TRUE);

#if defined(DUCHAMP)
\t/* DUCHAMP PRE-GIC COUNTER PROBE V1: sysreg reads only. */
\tint duchamp_counter_probe = 0;
\tif (duchamp_counter_probe == 1) {
\t\tfor (;;) {
\t\t\t__asm__ volatile("wfe" ::: "memory");
\t\t}
\t}
#endif

\tPE_init_platform(TRUE, &BootCpuData);
}
'''


class TimerProbeStageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.arm = self.root / "osfmk" / "arm"
        self.arm.mkdir(parents=True)
        self.source = self.arm / "arm_init.c"
        self.source.write_text(SOURCE, encoding="utf-8")

    def test_probe_is_opt_in_masked_and_precedes_platform_and_gic(self):
        transformed = MODULE.transform(SOURCE)
        self.assertEqual(transformed.count(MODULE.MARKER), 1)
        self.assertLess(
            transformed.index("duchamp_timer_probe == 1"),
            transformed.index('"CNTV_CVAL_EL0"'),
        )
        self.assertLess(
            transformed.index("DUCHAMP TIMER EXPIRY PROBE PASS"),
            transformed.index("PE_init_platform(TRUE"),
        )
        probe = transformed[
            transformed.index(MODULE.MARKER):
            transformed.index("PE_init_platform(TRUE")
        ]
        self.assertIn("DTPROBE_CTL_ENABLE | DTPROBE_CTL_IMASK", probe)
        self.assertIn('__builtin_arm_wsr64("CNTV_CTL_EL0", 0)', probe)
        self.assertEqual(
            re.findall(r'__builtin_arm_wsr64\("([A-Z0-9_]+)"', probe),
            ["CNTV_CVAL_EL0", "CNTV_CTL_EL0", "CNTV_CTL_EL0"],
        )
        for forbidden in ("GICD", "GICR", "ICC_", "smc", "ml_io_map",
                          "MMIO"):
            self.assertNotIn(forbidden, probe)

    def test_loop_has_iteration_and_elapsed_bounds(self):
        transformed = MODULE.transform(SOURCE)
        self.assertIn("polls < 10000000", transformed)
        self.assertIn("frequency / 10", transformed)
        self.assertIn("end - start > max_elapsed", transformed)
        self.assertEqual(transformed.count('for (;;) {'), 2)

    def test_disable_precedes_result_and_stop(self):
        transformed = MODULE.transform(SOURCE)
        disable = transformed.index('__builtin_arm_wsr64("CNTV_CTL_EL0", 0)')
        validate = transformed.index("dtprobe_expiry_check")
        stop = transformed.rindex('for (;;) {')
        self.assertLess(disable, validate)
        self.assertLess(validate, stop)

    def test_stage_is_idempotent(self):
        self.assertFalse(MODULE.stage(self.root)["already_staged"])
        before = {path.name: path.read_bytes() for path in self.arm.iterdir()}
        self.assertTrue(MODULE.stage(self.root)["already_staged"])
        after = {path.name: path.read_bytes() for path in self.arm.iterdir()}
        self.assertEqual(before, after)

    def test_changed_source_is_rejected(self):
        MODULE.stage(self.root)
        self.source.write_text(
            self.source.read_text(encoding="utf-8").replace(
                "polls < 10000000", "polls < 1"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "changed staged"):
            MODULE.stage(self.root)

    def test_counter_stage_is_required_without_writes(self):
        self.source.write_text(
            SOURCE.replace(MODULE.COUNTER_MARKER, "counter marker missing"),
            encoding="utf-8",
        )
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, "counter probe"):
            MODULE.stage(self.root)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse((self.arm / "duchamp_timer_probe.h").exists())

    def test_existing_header_is_preserved(self):
        header = self.arm / "duchamp_timer_probe.h"
        header.write_text("user file", encoding="utf-8")
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, "preserve existing"):
            MODULE.stage(self.root)
        self.assertEqual(header.read_text(encoding="utf-8"), "user file")
        self.assertEqual(self.source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
