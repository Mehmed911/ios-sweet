#!/usr/bin/env python3
"""Failure-atomicity and default-deny tests for Duchamp PSCI staging."""
import argparse,importlib.util,sys,tempfile,unittest
from pathlib import Path


spec=importlib.util.spec_from_file_location("psci_stage",Path(__file__).with_name("stage-duchamp-psci-boot.py"))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


class Guards(unittest.TestCase):
    source=None
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/"iokit/Kernel/arm/SweetCPU.cpp"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(self.source.read_bytes())
        self.header=self.path.with_name("duchamp_psci_boot.h")
    def test_default_deny_precedes_conduit(self):
        new=mod.transform(self.path.read_text())
        self.assertIn(mod.MARKER,new)
        self.assertIn("return 0;\n}\n\nstatic int\nduchamp_psci_conduit",new)
        self.assertIn("dpsci_cpu_on(&duchamp_psci_ops, &request, &rc)",new)
        caller=new[new.index("SweetCPU::startCPU"):new.index("SweetCPU::quiesceCPU")]
        duchamp=caller[caller.index("#if defined(DUCHAMP)"):caller.index("#else")]
        self.assertNotIn("rc = sweet_psci_cpu_on",duchamp)
        header=(Path(__file__).resolve().parent.parent/"duchamp/drivers/duchamp_psci_boot.h").read_text()
        self.assertLess(header.index("ops->authorise"),header.index("ops->conduit"))
    def test_idempotence(self):
        self.assertFalse(mod.stage(self.root)["already_staged"])
        before={path.name:path.read_bytes() for path in self.path.parent.iterdir()}
        self.assertTrue(mod.stage(self.root)["already_staged"])
        self.assertEqual(before,{path.name:path.read_bytes() for path in self.path.parent.iterdir()})
    def test_changed_body_rejected(self):
        mod.stage(self.root)
        self.path.write_text(self.path.read_text().replace("DPSCI_LOCAL_UNVERIFIED","0",1))
        with self.assertRaisesRegex(ValueError,"changed staged PSCI"):
            mod.stage(self.root)
    def test_changed_header_rejected(self):
        mod.stage(self.root);self.header.write_bytes(self.header.read_bytes()+b"\n")
        with self.assertRaises(ValueError):mod.stage(self.root)
    def test_preexisting_header_preserved(self):
        self.header.write_bytes(b"user header");before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.header.read_bytes(),b"user header")
        self.assertEqual(self.path.read_bytes(),before)
    def test_late_anchor_failure_has_no_writes(self):
        self.path.write_text(self.path.read_text().replace("__builtin_arm_dsb(DSB_SY);","changed barrier",1))
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(self.header.exists())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    args=parser.parse_args();Guards.source=args.source
    unittest.main(argv=[sys.argv[0]])
