#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/verify-duchamp-dma-iommu-probe.py"
ARTIFACTS = ROOT / "work/duchamp-dma-iommu-probe-v1"
MODULE = ARTIFACTS / "duchamp_dma_iommu_probe.ko.UNSAFE-DO-NOT-LOAD"
SYMVERS_RECEIPT = ARTIFACTS / "symvers-v4/receipt.json"
SOURCE = ROOT / "duchamp/diagnostics/dma-iommu-probe/duchamp_dma_iommu_probe.c"


def load_tool():
    spec = importlib.util.spec_from_file_location("verify_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifyProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_real_probe_is_rejected_for_struct_module_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(
                ValueError, "candidate=0x400, captured=0x440"
            ):
                self.tool.verify(
                    MODULE, SYMVERS_RECEIPT, SOURCE, Path(temporary) / "out"
                )

    def test_compiler_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "changed.ko"
            data = bytearray(MODULE.read_bytes())
            _, sections = self.tool.elf_layout(data)
            comment = sections[".comment"]["header"]
            data[comment[4] + 1] ^= 1
            changed.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "compiler"):
                self.tool.verify(
                    changed, SYMVERS_RECEIPT, SOURCE, Path(temporary) / "out"
                )

    def test_crc_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "changed.ko"
            data = bytearray(MODULE.read_bytes())
            _, sections = self.tool.elf_layout(data)
            versions = sections["__versions"]["header"]
            data[versions[4]] ^= 1
            changed.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "CRC"):
                self.tool.verify(
                    changed, SYMVERS_RECEIPT, SOURCE, Path(temporary) / "out"
                )

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.tool.verify(MODULE, SYMVERS_RECEIPT, SOURCE, output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
