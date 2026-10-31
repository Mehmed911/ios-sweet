#!/usr/bin/env python3
"""Staging corruption/idempotence guards against the real patched XNU source."""
import argparse,importlib.util,sys,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('gic_stage',Path(__file__).with_name('stage-duchamp-gic-boot.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Guards(unittest.TestCase):
    source=None
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.path=self.root/'pexpert/arm/pe_fiq.c';self.path.parent.mkdir(parents=True);self.path.write_bytes(self.source.read_bytes())
        for name in ['iokit/Kernel/arm/SweetCPU.cpp','iokit/KernelConfigTables.cpp']:
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((self.source.parents[2]/name).read_bytes())
        self.header=self.path.with_name('duchamp_gic_boot.h')
    def test_idempotence(self):
        self.assertFalse(mod.stage(self.root)['already_staged'])
        before={p.name:p.read_bytes() for p in self.path.parent.iterdir()}
        self.assertTrue(mod.stage(self.root)['already_staged'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.path.parent.iterdir()})
    def test_changed_header(self):
        mod.stage(self.root);self.header.write_bytes(self.header.read_bytes()+b'\n')
        with self.assertRaises(ValueError):mod.stage(self.root)
    def test_changed_c_body(self):
        mod.stage(self.root);self.path.write_text(self.path.read_text().replace('DGIC_MAX_POLLS','1'))
        with self.assertRaisesRegex(ValueError,'changed staged GIC'):mod.stage(self.root)
    def test_missing_receipt(self):
        mod.stage(self.root);self.path.with_name('duchamp_gic_boot.json').unlink()
        with self.assertRaises(ValueError):mod.stage(self.root)
    def test_preserve_preexisting_header(self):
        self.header.write_bytes(b'user header');before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.header.read_bytes(),b'user header');self.assertEqual(self.path.read_bytes(),before)
    def test_late_anchor_failure_no_writes(self):
        self.path.write_text(self.path.read_text().replace('// Mark this PE to be awake','// changed caller'))
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.path.read_bytes(),before);self.assertFalse(self.header.exists())
    def test_non_duchamp_body_retained(self):
        old=self.path.read_text();new=mod.transform(old)
        start=old.index('\t// Mark this PE to be awake\n');end=old.index('#if defined(SWEET)\n\t/*',start)
        self.assertIn('#else\n'+old[start:end]+'#endif /* DUCHAMP */',new)
        self.assertIn('if (phys_id == aff_value)',new)
    def test_cpu_binding_corruption_rejected(self):
        mod.stage(self.root);c=self.root/'iokit/KernelConfigTables.cpp';c.write_text(c.read_text().replace('arm,cortex-a510','bad,cpu'))
        with self.assertRaises(ValueError):mod.stage(self.root)
    def test_late_cpu_anchor_failure_no_writes(self):
        c=self.root/'iokit/Kernel/arm/SweetCPU.cpp';c.write_text(c.read_text().replace('Kryo 470','changed CPU'))
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.path.read_bytes(),before);self.assertFalse(self.header.exists())
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,required=True);a=ap.parse_args()
    Guards.source=a.source;unittest.main(argv=[sys.argv[0]])
