#!/usr/bin/env python3
"""Guard tests for captured-file provenance, ELF bounds/calls and output preservation."""
import argparse,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import duchamp_saved_ufs as saved

REPO=Path(__file__).resolve().parent.parent
class Guards(unittest.TestCase):
    audit=None;sources=None
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)
    def test_wrong_artifact(self):
        p=self.path/'wrong.img';p.write_bytes(b'not the captured firmware')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):saved.boot_contents(p)
    def test_truncated_elf(self):
        with self.assertRaises(ValueError):saved.Elf(b'\x7fELF\x02\x01')
    def test_elf_table_bounds(self):
        data=bytearray((self.audit/'ufs-mediatek-mod.ko').read_bytes());data[40:48]=b'\xff'*8
        with self.assertRaises(ValueError):saved.Elf(bytes(data))
    def test_wrong_relocation_target(self):
        elf=saved.Elf((self.audit/'ufs-mediatek-mod.ko').read_bytes())
        with self.assertRaisesRegex(ValueError,'call relocation'):elf.call(0x23f4,'dma_set_mask')
    def test_truncated_cpio(self):
        with self.assertRaises(ValueError):saved.selected_cpio(b'070701'+b'0'*104)
    def test_unsupported_cpio(self):
        with self.assertRaises(ValueError):saved.selected_cpio(b'070702'+b'0'*104)
    def test_source_changed(self):
        p=self.path/'drivers/of/device.c';p.parent.mkdir(parents=True)
        p.write_bytes((self.sources/'drivers/of/device.c').read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'source blob mismatch'):saved.sources(REPO,self.path)
    def test_existing_output_preserved(self):
        sentinel=self.path/'user-file';sentinel.write_bytes(b'preserve me')
        command=[sys.executable,str(REPO/'tools/audit-duchamp-saved-ufs.py'),str(self.path)]
        for flag in ('--boot','--vendor-boot','--fdt','--sources','--firmware-dir'):command += [flag,'missing']
        r=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertIn('preserve existing output',r.stderr)
        self.assertEqual(list(self.path.iterdir()),[sentinel]);self.assertEqual(sentinel.read_bytes(),b'preserve me')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--sources',type=Path,required=True);a=ap.parse_args()
    Guards.audit=a.audit.resolve();Guards.sources=a.sources.resolve();unittest.main(argv=[sys.argv[0]])
