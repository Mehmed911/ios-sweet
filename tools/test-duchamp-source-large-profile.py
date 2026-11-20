#!/usr/bin/env python3
"""0BSD reject unreceipted kernels and code-patching options before VM creation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest',type=Path)
    a=ap.parse_args()
    receipt=a.manifest.resolve();record=json.loads(receipt.read_text());kernel=Path(record['kernel'])
    spec=importlib.util.spec_from_file_location('source_large',Path(__file__).with_name('qemu-service-ram.py'))
    vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)

    class Gates(unittest.TestCase):
        def denied(self,**kwargs):
            with tempfile.TemporaryDirectory(prefix='duchamp-source-gates-',dir='/var/tmp') as tmp:
                dest=Path(tmp)/'must-not-create'
                with self.assertRaises(ValueError):
                    vm.run_vm(kernel,Path(tmp)/'absent-adt',Path(tmp)/'absent-root',dest,10,[],**kwargs)
                self.assertFalse(dest.exists())

        def test_current_source_kernel_requires_receipt(self):
            self.denied()

        def test_no_source_instruction_patches(self):
            self.denied(kernel_manifest=receipt,display_hz=120)

        def test_no_historical_debugger_patches(self):
            self.denied(kernel_manifest=receipt,debugger_script='not-a-real-script')

        def test_wrong_kernel_digest(self):
            with tempfile.TemporaryDirectory(prefix='duchamp-bad-receipt-',dir='/var/tmp') as tmp:
                path=Path(tmp)/'bad.json';path.write_text(json.dumps({**record,'sha256':'0'*64}))
                self.denied(kernel_manifest=path)

        def bad_trace(self, **changes):
            with tempfile.TemporaryDirectory(prefix='duchamp-trace-gates-',dir='/var/tmp') as tmp:
                source=Path(__file__).with_name('duchamp-render-passive.gdb')
                config=dict(passive_only=True,kernel_sha256=record['sha256'],
                    source_trace_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
                config.update(changes)
                path=Path(tmp)/'trace.json';path.write_text(json.dumps(config))
                self.denied(kernel_manifest=receipt,passive_trace_config=path)

        def test_nonpassive_trace_denied(self):
            self.bad_trace(passive_only=False)

        def test_trace_wrong_kernel_denied(self):
            self.bad_trace(kernel_sha256='0'*64)

        def test_trace_wrong_observer_denied(self):
            self.bad_trace(source_trace_sha256='0'*64)

    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Gates))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
