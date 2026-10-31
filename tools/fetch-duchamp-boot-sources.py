#!/usr/bin/env python3
"""Fetch pinned public GIC/timer references without replacing differing files."""
import argparse,hashlib,urllib.request
from pathlib import Path
import duchamp_boot_profile as p
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    for name,digest in p.SOURCE_PINS.items():
        target=a.output/name
        blob=lambda d:hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
        if target.exists():
            if blob(target.read_bytes())!=digest:raise ValueError('preserve differing source: '+name)
            continue
        with urllib.request.urlopen('https://raw.githubusercontent.com/aosp-mirror/kernel_common/'+p.COMMIT+'/'+name,timeout=30) as r:data=r.read(8*1024*1024+1)
        if len(data)>8*1024*1024 or blob(data)!=digest:raise ValueError('source download pin differs')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(data)
    print(str(len(p.sources(a.output)))+' source Git blobs verified')
if __name__=='__main__':main()
