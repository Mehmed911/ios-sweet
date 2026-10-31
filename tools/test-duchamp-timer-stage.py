#!/usr/bin/env python3
"""Failure-atomicity and ordering tests for Duchamp CNTFRQ staging."""
import argparse,importlib.util,sys,tempfile,unittest
from pathlib import Path


spec=importlib.util.spec_from_file_location("timer_stage",Path(__file__).with_name("stage-duchamp-timer-boot.py"))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


class Guards(unittest.TestCase):
    source=None
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/"osfmk/arm/arm_init.c"
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(self.source.read_bytes())
        self.header=self.path.with_name("duchamp_timer_boot.h")
    def test_check_precedes_timebase_init(self):
        new=mod.transform(self.path.read_text())
        self.assertIn(mod.MARKER,new)
        self.assertEqual(new.count('__builtin_arm_rsr64("CNTFRQ_EL0")'),1)
        self.assertLess(new.index("dtimer_frequency_check"),new.index("cpu_timebase_init(TRUE)"))
        self.assertLess(new.index("panic(\"DUCHAMP TIMER"),new.index("cpu_timebase_init(TRUE)"))
    def test_idempotence(self):
        self.assertFalse(mod.stage(self.root)["already_staged"])
        before={path.name:path.read_bytes() for path in self.path.parent.iterdir()}
        self.assertTrue(mod.stage(self.root)["already_staged"])
        self.assertEqual(before,{path.name:path.read_bytes() for path in self.path.parent.iterdir()})
    def test_changed_body_rejected(self):
        mod.stage(self.root)
        self.path.write_text(self.path.read_text().replace("DTIMER_OK","0",1))
        with self.assertRaisesRegex(ValueError,"changed staged timer"):
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
        self.path.write_text(self.path.read_text().replace("cpu_timebase_init(TRUE);","changed call",1))
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):mod.stage(self.root)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(self.header.exists())


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    args=parser.parse_args();Guards.source=args.source
    unittest.main(argv=[sys.argv[0]])
