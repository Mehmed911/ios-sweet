#!/usr/bin/env python3
"""Check invalid timing profiles, explicit pins and preservation before VM launch."""
import subprocess,sys,tempfile,unittest
from pathlib import Path

REPO=Path(__file__).resolve().parent.parent
class Guards(unittest.TestCase):
    def run_tool(self,name,*args):
        return subprocess.run([sys.executable,str(REPO/'tools'/name),*map(str,args)],capture_output=True,text=True)
    def test_negative_shift(self):
        r=self.run_tool('qemu-sweet.py','--icount-shift','-1')
        self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr)
    def test_large_shift(self):
        r=self.run_tool('qemu-sweet.py','--icount-shift','11')
        self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr)
    def arguments(self,output,kernel):
        return ['--kernel',kernel,'--reference','missing','--adt','missing','--hfsplus','missing',
                '--output',output,'--kernel-sha256','0'*64,'--root-sha256','0'*64]
    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as scratch:
            p=Path(scratch);marker=p/'user-file';marker.write_bytes(b'keep')
            r=self.run_tool('test-duchamp-system-boot.py',*self.arguments(p,'missing'))
            self.assertEqual(r.returncode,2);self.assertIn('preserve existing output',r.stderr)
            self.assertEqual(list(p.iterdir()),[marker]);self.assertEqual(marker.read_bytes(),b'keep')
    def test_kernel_pin_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as scratch:
            p=Path(scratch);kernel=p/'kernel';kernel.write_bytes(b'wrong kernel');out=p/'new'
            r=self.run_tool('test-duchamp-system-boot.py',*self.arguments(out,kernel))
            self.assertEqual(r.returncode,2);self.assertIn('explicit kernel/root pin differs',r.stderr)
            self.assertFalse(out.exists());self.assertEqual(kernel.read_bytes(),b'wrong kernel')
if __name__=='__main__':unittest.main()
