#!/usr/bin/env python3
"""Audit saved boot policy without disclosing complete command lines."""
import argparse,json
from pathlib import Path
import duchamp_boot_policy as policy

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path);ap.add_argument('--sources',type=Path,required=True)
    ap.add_argument('--boot',type=Path,required=True);ap.add_argument('--vendor-boot',type=Path,required=True)
    ap.add_argument('--fdt',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():ap.error('preserve existing output')
    before=policy.sources(a.sources)
    result=policy.inspect(a.boot,a.vendor_boot,a.fdt,a.sources);result['source_receipts']=before
    if before!=policy.sources(a.sources):raise ValueError('source inputs changed')
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
