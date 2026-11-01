#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/prepare-duchamp-probe-symvers.py"
MODULES = ROOT / "research/mt6897-contract/saved-v1"


def load_tool():
    spec = importlib.util.spec_from_file_location("prepare_probe_symvers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeSymversTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_real_captured_modules_provide_every_required_crc(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            receipt = self.tool.prepare(MODULES, output)
            self.assertEqual(
                set(receipt["symbols"]), set(self.tool.REQUIRED_SYMBOLS)
            )
            lines = (output / "Module.symvers").read_text().splitlines()
            self.assertEqual(len(lines), len(self.tool.REQUIRED_SYMBOLS))
            self.assertTrue(all(line.startswith("0x") for line in lines))
            self.assertTrue(all(len(line.split("\t")) == 5 for line in lines))
            self.assertTrue(all(line.endswith("\t") for line in lines))
            self.assertEqual(receipt["report_version"], 4)
            self.assertEqual(receipt["module_contract"]["this_module_bytes"], 0x440)
            self.assertEqual(
                receipt["module_contract"]["this_module_relocation_offsets"],
                [0x170, 0x3D8],
            )
            self.assertTrue(
                all(
                    module["this_module_bytes"] == 0x440
                    for module in receipt["modules"].values()
                )
            )
            self.assertTrue(
                all(
                    module["this_module_relocation_offsets"] == [0x170, 0x3D8]
                    for module in receipt["modules"].values()
                )
            )
            self.assertTrue(receipt["safety"]["offline_only"])
            self.assertFalse(receipt["safety"]["module_loading"])

    def test_tampered_pinned_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            modules = Path(temporary) / "modules"
            modules.mkdir()
            for name in self.tool.PINNED_MODULES:
                data = (MODULES / name).read_bytes()
                if name == "iommu_debug.ko":
                    data = data[:-1] + bytes([data[-1] ^ 1])
                (modules / name).write_bytes(data)
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                self.tool.prepare(modules, Path(temporary) / "out")

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.tool.prepare(MODULES, output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_wrong_vermagic_is_rejected(self):
        data = (MODULES / "ufs-mediatek-dbg.ko").read_bytes()
        old = self.tool.VERMAGIC.encode()
        replacement = ("x" * len(self.tool.VERMAGIC)).encode()
        self.assertIn(old, data)
        with self.assertRaisesRegex(ValueError, "vermagic"):
            self.tool.parse_module(data.replace(old, replacement, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
