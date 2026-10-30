#!/usr/bin/env python3
"""Staging ownership/idempotence/failure-atomicity tests; no kernel or phone required."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
REPO=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('backend_stage',Path(__file__).with_name('stage-duchamp-qemu-backends.py'))
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)

class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        (self.root/'bsd/conf').mkdir(parents=True);(self.root/'bsd/dev').mkdir()
        (self.root/'iokit/bsddev').mkdir(parents=True)
        self.config=self.root/'bsd/conf/files';self.cpp=self.root/'iokit/bsddev/IOKitBSDInit.cpp'
        self.config.write_text('bsd/dev/duchamp_qemu_ufs.c\t\tstandard\n')
        self.cpp.write_text('DUCHAMP QUFS ROOT SELECTED\n\t\tint qufs_error = duchamp_qemu_ufs_rootdev(root);\n')
    def snapshot(self):
        return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
    def rejected_unchanged(self):
        before=self.snapshot()
        with self.assertRaises(ValueError):stage.stage(self.root)
        self.assertEqual(before,self.snapshot())
    def test_fresh(self):
        result=stage.stage(self.root)
        self.assertFalse(result['already_staged'])
        self.assertEqual(len(result['files']),14)
        self.assertIn('backend_error',self.cpp.read_text())
        for name,digest in result['files'].items():
            import hashlib
            self.assertEqual(hashlib.sha256((self.root/name).read_bytes()).hexdigest(),digest)
    def test_idempotent(self):
        stage.stage(self.root);before=self.snapshot()
        self.assertTrue(stage.stage(self.root)['already_staged'])
        self.assertEqual(before,self.snapshot())
    def test_existing_unowned(self):
        (self.root/'bsd/dev/mt6897_v7s.h').write_text('user source')
        self.rejected_unchanged()
    def test_missing_ufs_stage(self):
        self.cpp.write_text('unrelated source')
        self.rejected_unchanged()
    def test_ambiguous_anchor(self):
        self.config.write_text(self.config.read_text()*2)
        self.rejected_unchanged()
    def test_changed_owned(self):
        stage.stage(self.root)
        p=self.root/'bsd/dev/mt6897_v7s.c';p.write_text(p.read_text()+'changed')
        self.rejected_unchanged()
    def test_partial(self):
        self.cpp.write_text(self.cpp.read_text()+'DUCHAMP QEMU backend selftest failed')
        self.rejected_unchanged()
    def test_all_workflow_core_globs_staged(self):
        result=stage.stage(self.root)
        expected={p.name for glob in ('mt6897*.c','mt6897*.h') for p in (REPO/'duchamp/drivers').glob(glob)}
        actual={Path(p).name for p in result['files'] if p.startswith('bsd/dev/mt6897')}
        self.assertEqual(expected,actual)

if __name__=='__main__':unittest.main()
