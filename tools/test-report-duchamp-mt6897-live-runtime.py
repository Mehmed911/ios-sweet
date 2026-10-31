#!/usr/bin/env python3
"""Unit tests for the offline Duchamp live-runtime evidence parser."""

import importlib.util
from pathlib import Path
import struct
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

    def test_iomem_claim_must_match_exact_range_and_owner(self):
        rows = self.module.parse_iomem(
            "0c400000-0c43ffff : GICD\n"
            "0c440000-0c63ffff : GICR\n"
            "112b0000-112b2fff : 112b0000.ufshci ufshci@112b0000\n"
        )
        claim = self.module.require_iomem_claim(rows, 0x112B0000, 0x3000, "ufshci")
        self.assertEqual(claim["start"], "0x112b0000")
        self.assertEqual(claim["end"], "0x112b2fff")
        with self.assertRaisesRegex(ValueError, "missing unique"):
            self.module.require_iomem_claim(rows, 0x112B0000, 0x4000, "ufshci")

    def test_build_id_and_loaded_module_are_parsed(self):
        raw = bytes.fromhex(
            "040000001400000003000000474e5500"
            "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84"
        )
        self.assertEqual(
            self.module.parse_gnu_build_id(raw),
            "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84",
        )
        module = self.module.parse_loaded_module(
            "ufs_mediatek_mod 14319616 24 mi_memory,rpmb_mtk, Live 0x0 (OE)\n",
            "ufs_mediatek_mod",
        )
        self.assertEqual(module["bytes"], 14319616)
        self.assertEqual(module["dependencies"], ["mi_memory", "rpmb_mtk"])
        self.assertEqual(module["taints"], "OE")

    def test_saved_module_identity_requires_exact_build_id(self):
        receipt = {
            "bytes": 14657944,
            "sha256": "7043e1109b4c356a914fdc92ffbe463c0c43cb27342f6ccce1517a2086b02493",
            "gnu_build_id": "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84",
        }
        matched = self.module.verify_saved_module_identity(
            "df7eecc22450fb6e6eceaaef4b3fe8ceb46b2a84", receipt
        )
        self.assertTrue(matched["build_id_match_verified"])
        self.assertFalse(matched["source_commit_match_verified"])
        with self.assertRaisesRegex(ValueError, "build IDs differ"):
            self.module.verify_saved_module_identity("00" * 20, receipt)

    def test_supplier_parser_keeps_only_supplier_links(self):
        links = self.module.parse_supplier_links(
            "/sys/devices/x/supplier:platform:10000000.syscon\n"
            "/sys/devices/x/of_node\n"
            "/sys/devices/x/supplier:phy:phy-112a0000.ufsphy.3\n"
        )
        self.assertEqual(
            links,
            [
                "supplier:phy:phy-112a0000.ufsphy.3",
                "supplier:platform:10000000.syscon",
            ],
        )

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

    def test_dma_range_decoder_reports_identity_64gib_window(self):
        class FakeNode:
            def __init__(self, path, parent=None, props=None):
                self.path = path
                self.parent = parent
                self.props = props or {}

            def cells(self, key):
                raw = self.props.get(key, b"")
                return list(struct.unpack(f">{len(raw) // 4}I", raw))

            def scalar(self, key, default=None):
                if key not in self.props:
                    return default
                values = self.cells(key)
                if len(values) != 1:
                    raise ValueError("not scalar")
                return values[0]

        root = FakeNode("/", props={"#address-cells": struct.pack(">I", 2)})
        soc = FakeNode(
            "/soc",
            parent=root,
            props={
                "#address-cells": struct.pack(">I", 2),
                "#size-cells": struct.pack(">I", 2),
                "dma-ranges": struct.pack(">6I", 0, 0, 0, 0, 0x10, 0),
            },
        )
        self.assertEqual(
            self.module.decode_dma_ranges(soc),
            [
                {
                    "child_bus_start": "0x0",
                    "parent_bus_start": "0x0",
                    "bytes": "0x1000000000",
                    "identity": True,
                }
            ],
        )

    def test_dma_range_decoder_rejects_partial_tuple(self):
        class FakeNode:
            def __init__(self, path, parent=None, props=None):
                self.path = path
                self.parent = parent
                self.props = props or {}

            def cells(self, key):
                raw = self.props.get(key, b"")
                return list(struct.unpack(f">{len(raw) // 4}I", raw))

            def scalar(self, key, default=None):
                if key not in self.props:
                    return default
                return self.cells(key)[0]

        root = FakeNode("/", props={"#address-cells": struct.pack(">I", 2)})
        soc = FakeNode(
            "/soc",
            parent=root,
            props={
                "#address-cells": struct.pack(">I", 2),
                "#size-cells": struct.pack(">I", 2),
                "dma-ranges": struct.pack(">I", 0),
            },
        )
        with self.assertRaisesRegex(ValueError, "unsupported dma-ranges"):
            self.module.decode_dma_ranges(soc)


if __name__ == "__main__":
    unittest.main(verbosity=2)
