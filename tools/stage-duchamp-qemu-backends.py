#!/usr/bin/env python3
"""Stage source-pinned backend/table cores and opt-in RAM selftest into XNU."""
import argparse
import hashlib
import json
from pathlib import Path


def stage(root):
    repo=Path(__file__).resolve().parent.parent
    names=['mt6897_backends.h','mt6897_ufs_platform.h','mt6897_ufs_dma.h',
           'mt6897_ufs_clocks.h','mt6897_v7s.h','mt6897_pmif.c','mt6897_pmic.c',
           'mt6897_firmware.c','mt6897_iommu.c','mt6897_ufs_platform.c',
           'mt6897_ufs_dma.c','mt6897_ufs_clocks.c','mt6897_v7s.c']
    paths={'bsd/dev/'+n:repo/'duchamp/drivers'/n for n in names}
    paths['bsd/dev/duchamp_qemu_backends.c']=repo/'duchamp/xnu/qemu_backends.c'
    config=root/'bsd/conf/files';iokit=root/'iokit/bsddev/IOKitBSDInit.cpp'
    c=config.read_text();i=iokit.read_text()
    additions=''.join(n+'\t\tstandard\n' for n in paths if n.endswith('.c'))
    marker='DUCHAMP QEMU backend selftest failed'
    hashes={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()}
    if marker in i:
        if additions not in c or any(not (root/n).is_file() or (root/n).read_bytes()!=p.read_bytes()
                                     for n,p in paths.items()):
            raise ValueError('partial/changed existing backend integration')
        return {'already_staged':True,'files':hashes}
    if 'DUCHAMP QUFS ROOT SELECTED' not in i:
        raise ValueError('stage established QEMU UFS integration first')
    anchor='bsd/dev/duchamp_qemu_ufs.c\t\tstandard\n'
    needle='\t\tint qufs_error = duchamp_qemu_ufs_rootdev(root);'
    if c.count(anchor)!=1 or i.count(needle)!=1 or any((root/n).exists() for n in paths):
        raise ValueError('unexpected source anchor or existing unowned file')
    replacement='''\t\textern int duchamp_qemu_backends_prepare(void);
\t\tint backend_error = duchamp_qemu_backends_prepare();
\t\tif (backend_error) {
\t\t\tpanic("DUCHAMP QEMU backend selftest failed: %d", backend_error);
\t\t}
'''+needle
    new_c=c.replace(anchor,anchor+additions,1);new_i=i.replace(needle,replacement,1)
    for n,p in paths.items():
        (root/n).write_bytes(p.read_bytes())
    config.write_text(new_c);iokit.write_text(new_i)
    return {'already_staged':False,'files':hashes}


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('xnu',type=Path);args=ap.parse_args()
    try:print(json.dumps(stage(args.xnu.resolve()),indent=2))
    except (ValueError,OSError) as e:ap.exit(1,'backend staging failed: '+str(e)+'\n')
