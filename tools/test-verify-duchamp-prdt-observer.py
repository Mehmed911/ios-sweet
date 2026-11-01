#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/verify-duchamp-prdt-observer.py"
OLD_MODULE = (
    ROOT
    / "work/duchamp-dma-iommu-probe-v2-local-only/duchamp_dma_iommu_probe.ko"
)
RECEIPT = ROOT / "work/duchamp-ufs-prdt-observer-local-only/symvers-v2/receipt.json"
SOURCE = ROOT / "duchamp/diagnostics/ufs-prdt-observer/duchamp_ufs_prdt_observer.c"


def load_tool():
    spec = importlib.util.spec_from_file_location("verify_prdt_observer", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifyPrdtObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = load_tool()

    def test_unrelated_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "modinfo value for name"):
                self.tool.verify(
                    OLD_MODULE, RECEIPT, SOURCE, Path(temporary) / "out"
                )

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "out"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.tool.verify(OLD_MODULE, RECEIPT, SOURCE, output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_verifier_requires_exact_compiler_and_no_signature(self):
        self.assertIn("r487747c", self.tool.EXPECTED_COMPILER)
        self.assertEqual(
            self.tool.SIGNATURE_MARKER, b"~Module signature appended~\n"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
