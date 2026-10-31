#!/usr/bin/env python3
"""Guard malformed evidence, privacy allowlisting and output preservation."""
import json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
import duchamp_boot_policy as p

class Guards(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)
    def test_allowlist_keys_and_values(self):
        result=p.select('androidboot.serialno=PRIVATE panel=PRIVATE swiotlb=PRIVATE disable_dma32=on')
        self.assertEqual(result,{'selected':['disable_dma32=on'],'unrecognized_policy_values':1})
        self.assertNotIn('PRIVATE',json.dumps(result))
    def test_order_and_duplicates(self):
        self.assertEqual(p.select('swiotlb=force swiotlb=noforce swiotlb=force')['selected'],
                         ['swiotlb=force','swiotlb=noforce','swiotlb=force'])
    def test_merge_size_bound(self):
        value=p.merge('bootconfig','swiotlb=noforce',25)
        self.assertFalse(value['fits_without_truncation'])
        self.assertNotIn('swiotlb=noforce',value['selected_after_size_limit']['selected'])
        needed=len('bootconfig swiotlb=noforce')+1
        self.assertFalse(p.merge('bootconfig','swiotlb=noforce',needed-1)['fits_without_truncation'])
        self.assertTrue(p.merge('bootconfig','swiotlb=noforce',needed)['fits_without_truncation'])
        with self.assertRaises(ValueError):p.merge('','',1)
    def test_invalid_quoting_is_redacted(self):
        with self.assertRaisesRegex(ValueError,'^invalid command-line quoting$'):p.select('PRIVATE="')
    def test_changed_source(self):
        path=self.path/'kernel/dma/swiotlb.c';path.parent.mkdir(parents=True);path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'source pin mismatch'):p.sources(self.path)
        self.assertEqual(path.read_bytes(),b'changed')
    def test_truncated_header(self):
        with self.assertRaises(ValueError):p.vendor_fields(b'VNDRBOOT')
    def vendor(self):
        data=bytearray(8192);data[:8]=b'VNDRBOOT'
        for off,n in [(8,4),(12,4096),(2096,2128)]:struct.pack_into('<I',data,off,n)
        return data
    def test_nonempty_bootconfig_never_claims_absence(self):
        data=self.vendor();struct.pack_into('<I',data,2124,12);data[4096:4108]=b'PRIVATE_DATA'
        result=p.vendor_fields(data)
        self.assertFalse(result['bootconfig_kernel_overrides_absent_in_saved_section'])
        self.assertNotIn('PRIVATE',json.dumps(result))
    def test_bootconfig_bounds(self):
        data=self.vendor();struct.pack_into('<I',data,2124,1000000)
        with self.assertRaisesRegex(ValueError,'out of bounds'):p.vendor_fields(data)
    def test_preserve_existing_output(self):
        sentinel=self.path/'user';sentinel.write_bytes(b'preserve')
        repo=Path(__file__).resolve().parent.parent
        args=[sys.executable,str(repo/'tools/audit-duchamp-boot-policy.py'),str(self.path)]
        for flag in ['--sources','--boot','--vendor-boot','--fdt']:args.extend([flag,'missing'])
        r=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(r.returncode,2);self.assertIn('preserve existing output',r.stderr)
        self.assertEqual(list(self.path.iterdir()),[sentinel]);self.assertEqual(sentinel.read_bytes(),b'preserve')
if __name__=='__main__':unittest.main()
