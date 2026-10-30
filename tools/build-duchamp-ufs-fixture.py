#!/usr/bin/env python3
"""Build a fresh offline HFS+ fixture/ADT/static PID1 for read-only virtual UFS."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import qemu_ufs


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    ap.add_argument('--base-root',type=Path,required=True)
    ap.add_argument('--adt',type=Path,required=True)
    ap.add_argument('--hfsplus',type=Path,required=True)
    ap.add_argument('--init-source',type=Path,default=Path(__file__).with_name('duchamp-ufs-init.S'))
    args=ap.parse_args()
    out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
    repo=Path(__file__).resolve().parent.parent
    original=args.base_root.read_bytes()
    if len(original)%4096 or original[1024:1026]!=b'H+':
        ap.error('base must be a regular aligned HFS+ image')
    root=out/'root.hfs'; root.write_bytes(original)
    expected=hashlib.sha256(b'duchamp-ufs-read-only-fixture-v1').digest()*32
    (out/'ufs-expected.bin').write_bytes(expected)
    init_source=args.init_source.resolve()
    subprocess.run(['clang','-target','arm64-apple-ios16.0','-c',str(init_source),
                    '-o',str(out/'init.o')],cwd=out,check=True)
    subprocess.run(['python3',str(repo/'tools/mkinit.py'),str(out/'init.o'),str(out/'launchd')],check=True)
    def hfs(*command):
        return subprocess.run([str(args.hfsplus.resolve()),str(root),*command],check=True,capture_output=True).stdout
    listing=hfs('ls','/').decode(errors='replace')
    if not re.search(r'(?m)^04[0-7]+\s+\d+\s+\d+\s+.*\sdev$',listing):
        hfs('mkdir','/dev')
    hfs('chmod','/dev','755')
    hfs('add',str(out/'launchd'),'/sbin/launchd'); hfs('chmod','/sbin/launchd','755')
    hfs('add',str(out/'ufs-expected.bin'),'/ufs-test.bin')
    for guest,source in [('/sbin/launchd',out/'launchd'),('/ufs-test.bin',out/'ufs-expected.bin')]:
        dest=out/('verified-'+source.name)
        hfs('extract',guest,str(dest))
        if dest.read_bytes()!=source.read_bytes():
            raise RuntimeError('HFS round-trip mismatch: '+guest)
    after=hfs('ls','/').decode(errors='replace')
    if not re.search(r'(?m)^04[0-7]+\s+\d+\s+\d+\s+.*\sdev$',after):
        raise RuntimeError('missing /dev mountpoint')
    tree=qemu_ufs.build_tree(args.adt.read_bytes())
    (out/'qemu-ufs.adt').write_bytes(tree)
    report={'scope':'offline fixture only; no VM or phone run',
        'base_sha256':hashlib.sha256(original).hexdigest(),
        'base_unchanged':args.base_root.read_bytes()==original,
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  [root,out/'launchd',out/'ufs-expected.bin',out/'qemu-ufs.adt']},
        'root_bytes':len(original),'no_ramdisk':True,'readonly_backend':True,
        'init_source':str(init_source),
        'init_source_sha256':hashlib.sha256(init_source.read_bytes()).hexdigest()}
    if not report['base_unchanged']: raise RuntimeError('base root changed')
    (out/'fixture.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
