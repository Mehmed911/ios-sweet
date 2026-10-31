#!/usr/bin/env python3
"""Fetch pinned boot-policy sources; preserve any differing existing files."""
import argparse,hashlib,urllib.request
from pathlib import Path
import duchamp_boot_policy as p
from duchamp_saved_ufs import GKI

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);a=ap.parse_args()
    for path,expected in p.SOURCE_PINS.items():
        target=a.output/path
        blob=lambda data:hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if target.exists():
            if blob(target.read_bytes())!=expected:raise ValueError('preserve differing source: '+path)
            continue
        with urllib.request.urlopen('https://raw.githubusercontent.com/aosp-mirror/kernel_common/'+GKI+'/'+path,timeout=30) as r:
            data=r.read(8*1024*1024+1)
        if len(data)>8*1024*1024 or blob(data)!=expected:raise ValueError('public source pin mismatch')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
    p.sources(a.output);print(str(len(p.SOURCE_PINS))+' pinned boot-policy sources verified')
if __name__=='__main__':main()
