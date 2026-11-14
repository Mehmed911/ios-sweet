#!/usr/bin/env python3
"""Check MCQ staging, idempotence and refusal of partial/user-owned trees."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "ufs_stage", Path(__file__).with_name("stage-duchamp-qemu-ufs.py"))
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class StageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in ("bsd/conf", "bsd/dev", "iokit/bsddev", "osfmk/arm"):
            (self.root / name).mkdir(parents=True)
        self.config = self.root / "bsd/conf/files"
        self.iokit = self.root / "iokit/bsddev/IOKitBSDInit.cpp"
        self.arm = self.root / "osfmk/arm/arm_init.c"
        self.config.write_text("bsd/dev/sweet_ufs.c\t\t\tstandard\n")
        self.iokit.write_text('QEMU RAM BLOCK READY\nMT6897 BACKEND STUB\n'
                              '\tif (strcmp(rdBootVar, "ufsroot0") == 0) {\n')
        self.arm.write_text("\tPE_init_platform(FALSE, args); /* Get platform expert set up */\n")

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def reject_unchanged(self):
        before = self.snapshot()
        with self.assertRaises(ValueError):
            stage.stage(self.root)
        self.assertEqual(before, self.snapshot())

    def test_complete_mcq_stage(self):
        result = stage.stage(self.root)
        self.assertFalse(result["already_staged"])
        self.assertEqual(len(result["files"]), 9)
        self.assertEqual(self.config.read_text().count(
            "bsd/dev/duchamp_qemu_ufs_mcq.c\t\tstandard\n"), 1)
        self.assertIn("dufs_mcq_bind(&qu.host,&setup)",
                      (self.root / "bsd/dev/duchamp_qemu_ufs.c").read_text())
        self.assertIn("dufs_snapshot_registers", (self.root /
                      "bsd/dev/duchamp_ufs_register_snapshot.c").read_text())

    def test_idempotent(self):
        stage.stage(self.root)
        before = self.snapshot()
        self.assertTrue(stage.stage(self.root)["already_staged"])
        self.assertEqual(before, self.snapshot())

    def test_existing_mcq_source(self):
        (self.root / "bsd/dev/duchamp_qemu_ufs_mcq.c").write_text("user source")
        self.reject_unchanged()

    def test_changed_mcq_source(self):
        stage.stage(self.root)
        path = self.root / "bsd/dev/duchamp_qemu_ufs_mcq.c"
        path.write_text(path.read_text() + "\n/* user change */\n")
        self.reject_unchanged()

    def test_existing_observer_source(self):
        (self.root / "bsd/dev/duchamp_ufs_register_snapshot.c").write_text("user source")
        self.reject_unchanged()

    def test_changed_observer_header(self):
        stage.stage(self.root)
        path = self.root / "bsd/dev/ufs_register_snapshot.h"
        path.write_text(path.read_text() + "\n/* user change */\n")
        self.reject_unchanged()

    def test_partial_old_integration(self):
        self.iokit.write_text(self.iokit.read_text() + "DUCHAMP QUFS ROOT SELECTED\n")
        self.reject_unchanged()

    def test_missing_arm_anchor(self):
        self.arm.write_text("unrelated source")
        self.reject_unchanged()

    def test_duplicate_config_anchor(self):
        self.config.write_text(self.config.read_text() * 2)
        self.reject_unchanged()


if __name__ == "__main__":
    unittest.main()
