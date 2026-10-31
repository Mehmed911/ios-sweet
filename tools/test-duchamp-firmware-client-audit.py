#!/usr/bin/env python3
"""Mutation/provenance guards for saved UFS client and comparison firmware audit."""
import argparse,importlib.util,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('fw_audit',Path(__file__).with_name('audit-duchamp-firmware-client.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
class Guards(unittest.TestCase):
    data=None;reference=None
    def changed(self,offset,word):
        data=bytearray(self.data);elf=audit.saved.Elf(data);base=elf.headers[elf.sections['.text']][4]
        struct.pack_into('<I',data,base+offset,word);return audit.saved.Elf(data)
    def test_real_client(self):
        result=audit.inspect_client(audit.saved.Elf(self.data));self.assertEqual(result['control_allocations']['alignment_bytes'],[128,1024,1024])
    def test_wrong_selector(self):
        with self.assertRaises(ValueError):audit.inspect_client(self.changed(0x1e78,0x52800001))
    def test_wrong_result_register(self):
        with self.assertRaises(ValueError):audit.inspect_client(self.changed(0x1e84,0xf94023e8))
    def test_changed_alloc_attrs(self):
        with self.assertRaises(ValueError):audit.inspect_client(self.changed(0x13200,0xd503201f))
    def test_changed_align_check(self):
        with self.assertRaises(ValueError):audit.inspect_client(self.changed(0x131e4,0xd503201f))
    def test_wrong_call_relocation(self):
        elf=audit.saved.Elf(self.data);elf.symbols=[('wrong_target' if s[0]=='dmam_alloc_attrs' else s[0],*s[1:]) for s in elf.symbols]
        with self.assertRaises(ValueError):audit.inspect_client(elf)
    def test_bad_module_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad';p.write_bytes(b'not saved module')
            with self.assertRaises(ValueError):audit.saved.pinned(p,audit.saved.UFS_SHA)
    def test_reference_pin(self):
        with self.assertRaises(ValueError):audit.reference.check(self.reference+b'changed')
    def test_preserve_output(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);sentinel=p/'user';sentinel.write_bytes(b'keep')
            r=subprocess.run([sys.executable,str(Path(audit.__file__)),str(p),'--saved-audit','missing','--sources','missing','--reference','missing'],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertIn('preserve existing output',r.stderr);self.assertEqual(sentinel.read_bytes(),b'keep')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--saved-audit',type=Path,required=True)
    ap.add_argument('--reference',type=Path,required=True);a=ap.parse_args()
    Guards.data=audit.saved.pinned(a.saved_audit/'ufs-mediatek-mod.ko',audit.saved.UFS_SHA)
    Guards.reference=(a.reference/'ufs_ctrl.c').read_bytes();audit.reference.check(Guards.reference)
    unittest.main(argv=[sys.argv[0]])
