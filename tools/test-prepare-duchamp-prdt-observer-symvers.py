#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/prepare-duchamp-prdt-observer-symvers.py"
MODULES = ROOT / "research/mt6897-contract/saved-v1"


def load_tool():
    spec = importlib.util.spec_from_file_location("prepare_prdt_symvers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PreparePrdtObserverSymversTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_exact_captured_symbol_set_is_prepared(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            receipt = self.tool.prepare(MODULES, output)
            self.assertEqual(receipt["profile"], "duchamp-ufs-prdt-observer")
            self.assertEqual(
                set(receipt["symbols"]), set(self.tool.REQUIRED_SYMBOLS)
            )
            self.assertEqual(
                receipt["symbols"]["__tracepoint_android_vh_ufs_fill_prdt"][
                    "crc"
                ],
                "0x248c91f6",
            )
            self.assertEqual(
                receipt["symbols"]["tracepoint_probe_register"]["crc"],
                "0x95e102ab",
            )
            self.assertEqual(
                receipt["symbols"]["tracepoint_probe_unregister"]["crc"],
                "0xdbeeece6",
            )
            self.assertEqual(
                receipt["symbols"]["sg_next"]["crc"], "0x87b8798d"
            )
            self.assertEqual(
                receipt["symbols"]["memstart_addr"]["crc"], "0x9688de8b"
            )
            self.assertEqual(
                receipt["symbols"]["iommu_get_domain_for_dev"]["crc"],
                "0x825b0f1d",
            )
            self.assertEqual(
                receipt["symbols"]["synchronize_rcu"]["crc"], "0x6091797f"
            )
            self.assertEqual(
                receipt["symbols"]["synchronize_srcu"]["crc"], "0x5ee82342"
            )
            self.assertEqual(
                receipt["symbols"]["tracepoint_srcu"]["crc"], "0xc8063a7e"
            )
            self.assertEqual(receipt["module_contract"]["this_module_bytes"], 0x440)
            self.assertTrue((output / "Module.symvers").is_file())
            self.assertTrue((output / "receipt.json").is_file())

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.tool.prepare(MODULES, output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_all_symbols_have_captured_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt = self.tool.prepare(MODULES, Path(temporary) / "out")
            for details in receipt["symbols"].values():
                self.assertTrue(details["observed_in"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
