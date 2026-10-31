#!/usr/bin/env python3
"""Unit tests for the offline Duchamp live-runtime evidence parser."""

import importlib.util
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parent.parent


def load_module():
    path = REPO / "tools/report-duchamp-mt6897-live-runtime.py"
    spec = importlib.util.spec_from_file_location("duchamp_live_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def interrupts(timer, ufs):
    return "\n".join(
        (
            "           CPU0       CPU1",
            f" 20: {timer[0]:10d} {timer[1]:10d} GICv3  27 Level arch_timer",
            f"500: {ufs[0]:10d} {ufs[1]:10d} GICv3 200 Level ufshcd",
            f"509: {ufs[2]:10d} {ufs[3]:10d} GICv3 209 Level ufshcd",
        )
    )


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_parses_gic_timer_and_ufs_deltas(self):
        before = interrupts((100, 200), (10, 20, 30, 40))
        after = interrupts((103, 205), (11, 22, 34, 45))
        cpus, rows = self.module.interrupt_deltas(before, after)
        self.assertEqual(cpus, 2)
        by_irq = {row["linux_irq"]: row for row in rows}
        self.assertEqual(by_irq[20]["hwirq"], 27)
        self.assertEqual(by_irq[20]["total_delta"], 8)
        self.assertEqual(by_irq[500]["total_delta"], 3)
        self.assertEqual(by_irq[509]["total_delta"], 9)

    def test_counter_rollback_is_rejected(self):
        before = interrupts((100, 200), (10, 20, 30, 40))
        after = interrupts((99, 205), (11, 22, 34, 45))
        with self.assertRaisesRegex(ValueError, "moved backwards"):
            self.module.interrupt_deltas(before, after)

    def test_irq_identity_change_is_rejected(self):
        before = interrupts((100, 200), (10, 20, 30, 40))
        after = interrupts((103, 205), (11, 22, 34, 45)).replace(
            "GICv3 200 Level", "GICv3 201 Level"
        )
        with self.assertRaisesRegex(ValueError, "identity changed"):
            self.module.interrupt_deltas(before, after)

    def test_runtime_fdt_allowlist_is_narrow(self):
        self.assertEqual(len(self.module.ALLOWED_RUNTIME_FDT_CHANGES), 5)
        self.assertNotIn(
            ("/soc/ufshci@112b0000", "reg"),
            self.module.ALLOWED_RUNTIME_FDT_CHANGES,
        )
        self.assertNotIn(
            ("/interrupt-controller", "reg"),
            self.module.ALLOWED_RUNTIME_FDT_CHANGES,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
