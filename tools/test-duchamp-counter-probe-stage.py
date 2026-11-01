#!/usr/bin/env python3
"""Failure-atomicity and ordering tests for the pre-GIC counter probe."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("stage-duchamp-counter-probe.py")
SPEC = importlib.util.spec_from_file_location("counter_stage", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


SOURCE = '''#include <arm/cpu_internal.h>
#if defined(DUCHAMP)
#include <arm/duchamp_timer_boot.h>
#endif
void arm_init(void)
{
\tcpu_machine_idle_init(TRUE);

\tPE_init_platform(TRUE, &BootCpuData);
}
'''


class CounterStageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.arm = self.root / "osfmk" / "arm"
        self.arm.mkdir(parents=True)
        self.source = self.arm / "arm_init.c"
        self.source.write_text(SOURCE, encoding="utf-8")

    def test_probe_is_opt_in_and_precedes_platform_and_gic(self):
        transformed = MODULE.transform(SOURCE)
        self.assertEqual(transformed.count(MODULE.MARKER), 1)
        self.assertEqual(transformed.count('"CNTFRQ_EL0"'), 1)
        self.assertEqual(transformed.count('"CNTVCT_EL0"'), 2)
        self.assertLess(
            transformed.index("duchamp_counter_probe == 1"),
            transformed.index('"CNTFRQ_EL0"'),
        )
        self.assertLess(
            transformed.index("DUCHAMP COUNTER PROBE PASS"),
            transformed.index("PE_init_platform(TRUE"),
        )
        probe = transformed[
            transformed.index(MODULE.MARKER):
            transformed.index("PE_init_platform(TRUE")
        ]
        for forbidden in ("GICD", "GICR", "ICC_", "smc", "ml_io_map",
                          "__builtin_arm_wsr"):
            self.assertNotIn(forbidden, probe)

    def test_loop_is_bounded_and_success_and_failure_stop(self):
        transformed = MODULE.transform(SOURCE)
        self.assertIn("polls < 1000000", transformed)
        self.assertIn("DCOUNTER_OK", transformed)
        self.assertEqual(transformed.count('for (;;) {'), 1)
        self.assertIn('"wfe"', transformed)

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
                "polls < 1000000", "polls < 1"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "changed staged"):
            MODULE.stage(self.root)

    def test_existing_header_is_preserved(self):
        header = self.arm / "duchamp_counter_probe.h"
        header.write_text("user file", encoding="utf-8")
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, "preserve existing"):
            MODULE.stage(self.root)
        self.assertEqual(header.read_text(encoding="utf-8"), "user file")
        self.assertEqual(self.source.read_bytes(), before)

    def test_anchor_failure_has_no_writes(self):
        self.source.write_text(
            SOURCE.replace("cpu_machine_idle_init(TRUE);", "changed();"),
            encoding="utf-8",
        )
        before = self.source.read_bytes()
        with self.assertRaisesRegex(ValueError, "source anchor"):
            MODULE.stage(self.root)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse((self.arm / "duchamp_counter_probe.h").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
